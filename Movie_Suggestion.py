import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
from PIL import Image, ImageTk
from io import BytesIO
import random
import json
import os
import webbrowser
from datetime import datetime

class MovieSuggestionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Suggestion Machine")
        self.root.geometry("1200x800")
        
        # API configuration
        self.api_key = "a5b3bd888d774687933cce41d0a8aa30"  # Replace with your actual API key
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w500"
        
        # Streaming availability API (JustWatch)
        self.justwatch_url = "https://apis.justwatch.com/content/titles/en_US/popular"
        
        # User data
        self.current_user = None
        self.user_data_file = "user_data.json"
        self.user_preferences = {}
        self.watch_history = {}
        self.load_user_data()
        
        # Initialize data
        self.genres = []
        self.current_movie_details = None
        self.poster_image = None
        
        # Theme configuration
        self.dark_mode = False
        self.theme_colors = {
            "light": {
                "bg": "#f0f0f0", "fg": "#333333",
                "button_bg": "#e0e0e0", "button_fg": "#000000",
                "highlight": "#4CAF50", "text_bg": "#ffffff"
            },
            "dark": {
                "bg": "#2d2d2d", "fg": "#ffffff",
                "button_bg": "#3d3d3d", "button_fg": "#ffffff",
                "highlight": "#4CAF50", "text_bg": "#1e1e1e"
            }
        }
        
        # Create UI
        self.create_widgets()
        self.apply_theme()
        
        # Load genres
        self.load_genres()
        
        # Bind keyboard shortcuts
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
    
    # --------------------------
    # User Account Management
    # --------------------------
    def load_user_data(self):
        """Load user data from file"""
        if os.path.exists(self.user_data_file):
            with open(self.user_data_file, "r") as f:
                data = json.load(f)
                self.user_preferences = data.get("preferences", {})
                self.watch_history = data.get("history", {})
        else:
            self.user_preferences = {}
            self.watch_history = {}
    
    def save_user_data(self):
        """Save user data to file"""
        data = {
            "preferences": self.user_preferences,
            "history": self.watch_history
        }
        with open(self.user_data_file, "w") as f:
            json.dump(data, f, indent=4)
    
    def login_user(self):
        """Prompt user to login or create account"""
        username = simpledialog.askstring("Login", "Enter your username:")
        if username:
            self.current_user = username
            if username not in self.user_preferences:
                self.user_preferences[username] = {
                    "favorite_genres": [],
                    "preferred_streaming": [],
                    "rated_movies": {}
                }
            if username not in self.watch_history:
                self.watch_history[username] = []
            
            self.update_user_menu()
            messagebox.showinfo("Welcome", f"Logged in as {username}")
    
    def update_preferences(self):
        """Update user preferences dialog"""
        if not self.current_user:
            messagebox.showerror("Error", "Please login first")
            return
        
        # Create preferences dialog
        pref_window = tk.Toplevel(self.root)
        pref_window.title("Update Preferences")
        pref_window.geometry("400x300")
        
        # Favorite genres
        ttk.Label(pref_window, text="Favorite Genres:").pack(pady=5)
        self.genre_pref_vars = {}
        genre_frame = ttk.Frame(pref_window)
        genre_frame.pack()
        
        for i, genre in enumerate(self.genres):
            var = tk.BooleanVar(value=genre in self.user_preferences[self.current_user]["favorite_genres"])
            self.genre_pref_vars[genre] = var
            cb = ttk.Checkbutton(genre_frame, text=genre, variable=var)
            cb.grid(row=i//3, column=i%3, sticky="w", padx=5)
        
        # Streaming preferences
        ttk.Label(pref_window, text="Preferred Streaming Services:").pack(pady=5)
        streaming_services = ["Netflix", "Amazon Prime", "Disney+", "HBO Max", "Hulu"]
        self.streaming_pref_vars = {}
        streaming_frame = ttk.Frame(pref_window)
        streaming_frame.pack()
        
        for i, service in enumerate(streaming_services):
            var = tk.BooleanVar(value=service in self.user_preferences[self.current_user]["preferred_streaming"])
            self.streaming_pref_vars[service] = var
            cb = ttk.Checkbutton(streaming_frame, text=service, variable=var)
            cb.grid(row=i//3, column=i%3, sticky="w", padx=5)
        
        # Save button
        ttk.Button(pref_window, text="Save Preferences", 
                  command=lambda: self.save_preferences(pref_window)).pack(pady=10)
    
    def save_preferences(self, window):
        """Save user preferences"""
        if not self.current_user:
            return
        
        # Save genre preferences
        self.user_preferences[self.current_user]["favorite_genres"] = [
            genre for genre, var in self.genre_pref_vars.items() if var.get()
        ]
        
        # Save streaming preferences
        self.user_preferences[self.current_user]["preferred_streaming"] = [
            service for service, var in self.streaming_pref_vars.items() if var.get()
        ]
        
        self.save_user_data()
        window.destroy()
        messagebox.showinfo("Success", "Preferences updated successfully!")
    
    def update_user_menu(self):
        """Update the user menu with current user info"""
        if self.current_user:
            self.user_menu.entryconfig(0, label=f"Logged in as: {self.current_user}", state="disabled")
            self.user_menu.entryconfig(1, state="normal")  # Preferences
            self.user_menu.entryconfig(2, state="normal")  # Watch History
            self.user_menu.entryconfig(3, state="normal")  # Logout
        else:
            self.user_menu.entryconfig(0, label="Login", state="normal")
            self.user_menu.entryconfig(1, state="disabled")  # Preferences
            self.user_menu.entryconfig(2, state="disabled")  # Watch History
            self.user_menu.entryconfig(3, state="disabled")  # Logout
    
    # --------------------------
    # Streaming Availability
    # --------------------------
    def get_streaming_availability(self, movie_title):
        """Get streaming availability for a movie"""
        # Note: JustWatch API requires registration and has usage limits
        # This is a simplified demonstration
        
        if not self.current_user:
            return []
        
        # Get user's preferred services
        preferred_services = self.user_preferences[self.current_user]["preferred_streaming"]
        
        if not preferred_services:
            return []
        
        # In a real app, this would call the JustWatch API
        # For demo, we'll return mock data
        services = {
            "Netflix": "https://www.netflix.com",
            "Amazon Prime": "https://www.primevideo.com",
            "Disney+": "https://www.disneyplus.com",
            "HBO Max": "https://www.hbomax.com",
            "Hulu": "https://www.hulu.com"
        }
        
        # Return random available services for demo
        available = random.sample(preferred_services, min(2, len(preferred_services)))
        return [(s, services[s]) for s in available]
    
    # --------------------------
    # YouTube Trailer Integration
    # --------------------------
    def get_movie_trailer(self, movie_id):
        """Get YouTube trailer URL for a movie"""
        data = self.make_api_request(f"/movie/{movie_id}/videos")
        if data and data.get("results"):
            for video in data["results"]:
                if video["site"] == "YouTube" and video["type"] == "Trailer":
                    return f"https://www.youtube.com/watch?v={video['key']}"
        return None
    
    def play_trailer(self):
        """Play movie trailer in web browser"""
        if not self.current_movie_details:
            return
        
        trailer_url = self.get_movie_trailer(self.current_movie_details["id"])
        if trailer_url:
            webbrowser.open(trailer_url)
        else:
            messagebox.showinfo("No Trailer", "No trailer available for this movie")
    
    # --------------------------
    # Watch History Management
    # --------------------------
    def add_to_watch_history(self, movie_id):
        """Add movie to user's watch history"""
        if not self.current_user or not self.current_movie_details:
            return
        
        # Get current date
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add to history
        self.watch_history[self.current_user].append({
            "movie_id": movie_id,
            "title": self.current_movie_details["title"],
            "date_watched": now,
            "user_rating": None  # Can be set later
        })
        
        self.save_user_data()
    
    def show_watch_history(self):
        """Show user's watch history"""
        if not self.current_user:
            messagebox.showerror("Error", "Please login to view watch history")
            return
        
        history = self.watch_history.get(self.current_user, [])
        
        # Create history window
        history_window = tk.Toplevel(self.root)
        history_window.title("Your Watch History")
        history_window.geometry("600x400")
        
        # Create treeview
        history_tree = ttk.Treeview(
            history_window,
            columns=("title", "date_watched", "rating"),
            show="headings"
        )
        history_tree.heading("title", text="Title")
        history_tree.heading("date_watched", text="Date Watched")
        history_tree.heading("rating", text="Your Rating")
        
        history_tree.column("title", width=300)
        history_tree.column("date_watched", width=150)
        history_tree.column("rating", width=100)
        
        # Add history items
        for item in history:
            rating = item["user_rating"] if item["user_rating"] else "Not rated"
            history_tree.insert(
                "", tk.END,
                values=(item["title"], item["date_watched"], rating),
                iid=item["movie_id"]
            )
        
        # Bind double click to show movie details
        history_tree.bind("<Double-1>", lambda e: self.show_movie_from_history(e, history_window))
        
        # Add rating button
        rate_button = ttk.Button(
            history_window,
            text="Rate Selected Movie",
            command=lambda: self.rate_movie(history_tree)
        )
        
        # Pack widgets
        scrollbar = ttk.Scrollbar(history_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        history_tree.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=history_tree.yview)
        
        history_tree.pack(fill=tk.BOTH, expand=True)
        rate_button.pack(pady=10)
    
    def show_movie_from_history(self, event, window):
        """Show movie details from history selection"""
        tree = event.widget
        selected_item = tree.selection()
        if not selected_item:
            return
        
        movie_id = selected_item[0]
        self.show_movie_details(movie_id)
        window.destroy()
    
    def rate_movie(self, tree):
        """Rate a movie from watch history"""
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a movie to rate")
            return
        
        movie_id = selected_item[0]
        
        # Find movie in history
        for item in self.watch_history[self.current_user]:
            if str(item["movie_id"]) == movie_id:
                # Prompt for rating
                rating = simpledialog.askinteger(
                    "Rate Movie",
                    "Enter your rating (1-10):",
                    minvalue=1,
                    maxvalue=10
                )
                if rating:
                    item["user_rating"] = rating
                    self.save_user_data()
                    messagebox.showinfo("Success", "Rating saved!")
                    self.show_watch_history()  # Refresh
                break
    
    # --------------------------
    # Core Application Functions
    # --------------------------
    def make_api_request(self, endpoint, params=None):
        """Make a request to the TMDB API"""
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            messagebox.showerror("API Error", f"Failed to fetch data: {str(e)}")
            return None
    
    def get_genre_id(self, genre_name):
        """Get genre ID from name"""
        data = self.make_api_request("/genre/movie/list")
        if data:
            for genre in data["genres"]:
                if genre["name"].lower() == genre_name.lower():
                    return genre["id"]
        return None
    
    def load_genres(self):
        """Load movie genres from API"""
        data = self.make_api_request("/genre/movie/list")
        if data:
            self.genres = sorted([genre["name"] for genre in data["genres"]])
            self.genre_combobox["values"] = self.genres
            if self.genres:
                self.genre_combobox.current(0)
    
    def search_movies_by_genre(self, genre_name, page=1):
        """Search movies by genre"""
        genre_id = self.get_genre_id(genre_name)
        if not genre_id:
            return []
        
        params = {
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "page": page
        }
        data = self.make_api_request("/discover/movie", params)
        return data.get("results", []) if data else []
    
    def search_movies_by_query(self, query, page=1):
        """Search movies by query string"""
        params = {"query": query, "page": page}
        data = self.make_api_request("/search/movie", params)
        return data.get("results", []) if data else []
    
    def get_movie_details(self, movie_id):
        """Get detailed information about a specific movie"""
        return self.make_api_request(f"/movie/{movie_id}", {"append_to_response": "credits,videos"})
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # User menu
        self.user_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.user_menu.add_command(label="Login", command=self.login_user)
        self.user_menu.add_command(label="Preferences", command=self.update_preferences, state="disabled")
        self.user_menu.add_command(label="Watch History", command=self.show_watch_history, state="disabled")
        self.user_menu.add_command(label="Logout", command=self.logout_user, state="disabled")
        self.menu_bar.add_cascade(label="Account", menu=self.user_menu)
        
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for search/suggest
        self.left_panel = ttk.Frame(self.main_frame, width=350)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Right panel for movie details
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Search/Suggest controls
        self.create_search_controls()
        
        # Movie details display
        self.create_movie_details_display()
        
        # Theme toggle button
        self.theme_button = ttk.Button(
            self.root, 
            text="Toggle Dark Mode", 
            command=self.toggle_theme
        )
        self.theme_button.pack(side=tk.BOTTOM, pady=10)
    
    def create_search_controls(self):
        """Create search/suggestion controls"""
        # Notebook for tabs
        self.search_notebook = ttk.Notebook(self.left_panel)
        self.search_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Suggest Movies Tab
        self.suggest_frame = ttk.Frame(self.search_notebook)
        self.search_notebook.add(self.suggest_frame, text="Suggest")
        
        # Genre selection
        ttk.Label(self.suggest_frame, text="Select Genre:").pack(pady=5)
        self.genre_var = tk.StringVar()
        self.genre_combobox = ttk.Combobox(
            self.suggest_frame, 
            textvariable=self.genre_var,
            state="readonly"
        )
        self.genre_combobox.pack(fill=tk.X, pady=5)
        
        # Number of suggestions
        ttk.Label(self.suggest_frame, text="Number of Suggestions:").pack(pady=5)
        self.num_suggestions_var = tk.IntVar(value=5)
        ttk.Spinbox(
            self.suggest_frame,
            from_=1, to=20,
            textvariable=self.num_suggestions_var
        ).pack(fill=tk.X, pady=5)
        
        # Suggest button
        ttk.Button(
            self.suggest_frame, 
            text="Get Suggestions", 
            command=self.suggest_movies
        ).pack(fill=tk.X, pady=5)
        
        # Search Movies Tab
        self.search_frame = ttk.Frame(self.search_notebook)
        self.search_notebook.add(self.search_frame, text="Search")
        
        # Search entry
        ttk.Label(self.search_frame, text="Search Movies:").pack(pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            self.search_frame, 
            textvariable=self.search_var
        )
        self.search_entry.pack(fill=tk.X, pady=5)
        self.search_entry.bind("<Return>", lambda e: self.search_movies())
        
        # Search button
        ttk.Button(
            self.search_frame, 
            text="Search", 
            command=self.search_movies
        ).pack(fill=tk.X, pady=10)
        
        # Results frame
        self.results_frame = ttk.Frame(self.left_panel)
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Results treeview
        self.results_tree = ttk.Treeview(
            self.results_frame,
            columns=("title", "year", "rating"),
            show="headings",
            selectmode="browse"
        )
        self.results_tree.heading("title", text="Title")
        self.results_tree.heading("year", text="Year")
        self.results_tree.heading("rating", text="Rating")
        self.results_tree.column("title", width=200)
        self.results_tree.column("year", width=60)
        self.results_tree.column("rating", width=60)
        
        # Bind selection event
        self.results_tree.bind("<<TreeviewSelect>>", self.show_selected_movie_details)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_tree.yview)
        
        self.results_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_movie_details_display(self):
        """Create movie details display area"""
        # Top frame for poster and basic info
        self.details_top_frame = ttk.Frame(self.right_panel)
        self.details_top_frame.pack(fill=tk.X, pady=10)
        
        # Poster image
        self.poster_frame = ttk.Frame(self.details_top_frame, width=250, height=375)
        self.poster_frame.pack(side=tk.LEFT, padx=10)
        self.poster_frame.pack_propagate(False)
        
        self.poster_label = ttk.Label(self.poster_frame)
        self.poster_label.pack(fill=tk.BOTH, expand=True)
        
        # Basic info
        self.info_frame = ttk.Frame(self.details_top_frame)
        self.info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.title_label = ttk.Label(
            self.info_frame, 
            text="", 
            font=("Arial", 18, "bold"),
            wraplength=500
        )
        self.title_label.pack(anchor=tk.W, pady=5)
        
        self.meta_frame = ttk.Frame(self.info_frame)
        self.meta_frame.pack(anchor=tk.W, pady=5)
        
        self.year_label = ttk.Label(self.meta_frame, text="", font=("Arial", 10))
        self.year_label.pack(side=tk.LEFT, padx=5)
        
        self.rating_label = ttk.Label(self.meta_frame, text="", font=("Arial", 10))
        self.rating_label.pack(side=tk.LEFT, padx=5)
        
        self.runtime_label = ttk.Label(self.meta_frame, text="", font=("Arial", 10))
        self.runtime_label.pack(side=tk.LEFT, padx=5)
        
        self.genres_label = ttk.Label(
            self.info_frame, 
            text="", 
            wraplength=500
        )
        self.genres_label.pack(anchor=tk.W, pady=5)
        
        # Action buttons
        self.action_frame = ttk.Frame(self.info_frame)
        self.action_frame.pack(anchor=tk.W, pady=10)
        
        self.trailer_button = ttk.Button(
            self.action_frame,
            text="Watch Trailer",
            command=self.play_trailer
        )
        self.trailer_button.pack(side=tk.LEFT, padx=5)
        
        self.add_to_history_button = ttk.Button(
            self.action_frame,
            text="Add to Watch History",
            command=lambda: self.add_to_watch_history(self.current_movie_details["id"])
        )
        self.add_to_history_button.pack(side=tk.LEFT, padx=5)
        
        # Streaming availability
        self.streaming_frame = ttk.LabelFrame(self.info_frame, text="Available On")
        self.streaming_frame.pack(anchor=tk.W, fill=tk.X, pady=10)
        
        self.streaming_buttons = []
        
        # Overview
        ttk.Label(self.right_panel, text="Overview:", font=("Arial", 12)).pack(anchor=tk.W, pady=5)
        
        self.overview_text = tk.Text(
            self.right_panel,
            wrap=tk.WORD,
            height=5,
            state=tk.DISABLED
        )
        self.overview_text.pack(fill=tk.X, pady=5)
        
        # Cast
        ttk.Label(self.right_panel, text="Cast:", font=("Arial", 12)).pack(anchor=tk.W, pady=5)
        
        self.cast_text = tk.Text(
            self.right_panel,
            wrap=tk.WORD,
            height=8,
            state=tk.DISABLED
        )
        self.cast_text.pack(fill=tk.X, pady=5)
        
        # Crew
        ttk.Label(self.right_panel, text="Crew:", font=("Arial", 12)).pack(anchor=tk.W, pady=5)
        
        self.crew_text = tk.Text(
            self.right_panel,
            wrap=tk.WORD,
            height=4,
            state=tk.DISABLED
        )
        self.crew_text.pack(fill=tk.X, pady=5)
    
    def suggest_movies(self):
        """Suggest movies based on selected genre"""
        genre = self.genre_var.get()
        if not genre:
            messagebox.showerror("Error", "Please select a genre")
            return
        
        num_suggestions = self.num_suggestions_var.get()
        
        # Clear previous results
        self.results_tree.delete(*self.results_tree.get_children())
        
        # Get movies by genre
        movies = self.search_movies_by_genre(genre)
        
        if not movies:
            messagebox.showinfo("No Results", f"No movies found in the {genre} genre.")
            return
        
        # Add results to treeview
        for movie in random.sample(movies, min(num_suggestions, len(movies))):
            year = movie.get("release_date", "").split("-")[0] if movie.get("release_date") else "N/A"
            rating = movie.get("vote_average", "N/A")
            self.results_tree.insert(
                "", tk.END, 
                values=(movie["title"], year, rating),
                iid=str(movie["id"])
            )
        
        # Select first item
        if self.results_tree.get_children():
            self.results_tree.selection_set(self.results_tree.get_children()[0])
            self.results_tree.focus(self.results_tree.get_children()[0])
    
    def search_movies(self):
        """Search for movies by name"""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showerror("Error", "Please enter a search term")
            return
        
        # Clear previous results
        self.results_tree.delete(*self.results_tree.get_children())
        
        # Find matching movies
        movies = self.search_movies_by_query(query)
        
        if not movies:
            messagebox.showinfo("No Results", "No movies found matching your search.")
            return
        
        # Add results to treeview
        for movie in movies:
            year = movie.get("release_date", "").split("-")[0] if movie.get("release_date") else "N/A"
            rating = movie.get("vote_average", "N/A")
            self.results_tree.insert(
                "", tk.END, 
                values=(movie["title"], year, rating),
                iid=str(movie["id"])
            )
        
        # Select first item
        if self.results_tree.get_children():
            self.results_tree.selection_set(self.results_tree.get_children()[0])
            self.results_tree.focus(self.results_tree.get_children()[0])
    
    def show_selected_movie_details(self, event):
        """Show details for the selected movie"""
        selected_item = self.results_tree.selection()
        if not selected_item:
            return
        
        movie_id = selected_item[0]
        self.show_movie_details(movie_id)
    
    def show_movie_details(self, movie_id):
        """Display detailed information about a movie"""
        details = self.get_movie_details(movie_id)
        if not details:
            return
        
        self.current_movie_details = details
        
        # Update basic info
        self.title_label.config(text=details["title"])
        
        year = details.get("release_date", "").split("-")[0] if details.get("release_date") else "N/A"
        self.year_label.config(text=f"{year}")
        
        rating = details.get("vote_average", "N/A")
        self.rating_label.config(text=f"⭐ {rating}/10" if rating != "N/A" else "N/A")
        
        runtime = details.get("runtime", "N/A")
        self.runtime_label.config(text=f"⏱️ {runtime} min" if runtime != "N/A" else "N/A")
        
        genres = ", ".join([g["name"] for g in details.get("genres", [])])
        self.genres_label.config(text=genres)
        
        # Update streaming availability
        self.update_streaming_availability(details["title"])
        
        # Update overview
        self.overview_text.config(state=tk.NORMAL)
        self.overview_text.delete(1.0, tk.END)
        self.overview_text.insert(tk.END, details.get("overview", "No overview available."))
        self.overview_text.config(state=tk.DISABLED)
        
        # Update cast
        self.cast_text.config(state=tk.NORMAL)
        self.cast_text.delete(1.0, tk.END)
        cast = details.get("credits", {}).get("cast", [])
        for i, actor in enumerate(cast[:10], 1):  # Show top 10 cast members
            self.cast_text.insert(tk.END, f"{i}. {actor['name']} as {actor.get('character', 'N/A')}\n")
        self.cast_text.config(state=tk.DISABLED)
        
        # Update crew
        self.crew_text.config(state=tk.NORMAL)
        self.crew_text.delete(1.0, tk.END)
        crew = details.get("credits", {}).get("crew", [])
        directors = [p["name"] for p in crew if p["job"] == "Director"]
        if directors:
            self.crew_text.insert(tk.END, f"Director(s): {', '.join(directors)}\n\n")
        
        writers = [p["name"] for p in crew if p["job"] in ["Writer", "Screenplay"]]
        if writers:
            self.crew_text.insert(tk.END, f"Writer(s): {', '.join(writers)}\n")
        self.crew_text.config(state=tk.DISABLED)
        
        # Load poster image
        poster_path = details.get("poster_path")
        if poster_path:
            self.load_poster_image(poster_path)
        else:
            self.poster_label.config(image=None)
            self.poster_label.image = None
    
    def update_streaming_availability(self, movie_title):
        """Update streaming availability buttons"""
        # Clear existing buttons
        for button in self.streaming_buttons:
            button.destroy()
        self.streaming_buttons = []
        
        if not self.current_user:
            return
        
        # Get streaming availability
        available_services = self.get_streaming_availability(movie_title)
        
        if not available_services:
            no_service_label = ttk.Label(
                self.streaming_frame,
                text="Not available on your preferred services"
            )
            no_service_label.pack()
            self.streaming_buttons.append(no_service_label)
            return
        
        # Create buttons for each available service
        for service, url in available_services:
            button = ttk.Button(
                self.streaming_frame,
                text=service,
                command=lambda u=url: webbrowser.open(u)
            )
            button.pack(side=tk.LEFT, padx=5)
            self.streaming_buttons.append(button)
    
    def load_poster_image(self, poster_path):
        """Load and display movie poster"""
        try:
            response = requests.get(f"{self.image_base_url}{poster_path}")
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            
            # Resize image to fit in the frame
            img.thumbnail((250, 375))
            
            self.poster_image = ImageTk.PhotoImage(img)
            self.poster_label.config(image=self.poster_image)
        except Exception as e:
            print(f"Error loading image: {e}")
            self.poster_label.config(image=None)
    
    def logout_user(self):
        """Log out current user"""
        self.current_user = None
        self.update_user_menu()
        messagebox.showinfo("Logged Out", "You have been logged out")
    
    def toggle_theme(self):
        """Toggle between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.apply_theme()
    
    def apply_theme(self):
        """Apply the current theme colors"""
        theme = "dark" if self.dark_mode else "light"
        colors = self.theme_colors[theme]
        
        # Apply colors to all widgets
        self.root.config(bg=colors["bg"])
        
        # Configure style
        style = ttk.Style()
        style.theme_use("default")
        
        # Configure Treeview colors
        style.configure(
            "Treeview",
            background=colors["text_bg"],
            foreground=colors["fg"],
            fieldbackground=colors["text_bg"]
        )
        style.configure(
            "Treeview.Heading",
            background=colors["button_bg"],
            foreground=colors["button_fg"]
        )
        style.map(
            "Treeview",
            background=[('selected', colors["highlight"])],
            foreground=[('selected', colors["fg"])]
        )
        
        # Configure text widgets
        for widget in [self.overview_text, self.cast_text, self.crew_text]:
            widget.config(
                bg=colors["text_bg"],
                fg=colors["fg"],
                insertbackground=colors["fg"]
            )
        
        # Update all other widgets
        self.update_widget_colors(self.root, colors)
    
    def update_widget_colors(self, widget, colors):
        """Recursively update widget colors"""
        try:
            if isinstance(widget, (tk.Label, tk.Frame, ttk.Frame)):
                widget.config(
                    background=colors["bg"],
                    foreground=colors["fg"]
                )
        except tk.TclError:
            pass
        
        for child in widget.winfo_children():
            self.update_widget_colors(child, colors)
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        return "break"
    
    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode"""
        if self.fullscreen:
            self.fullscreen = False
            self.root.attributes("-fullscreen", False)
            return "break"

if __name__ == "__main__":
    root = tk.Tk()
    app = MovieSuggestionApp(root)
    root.mainloop()