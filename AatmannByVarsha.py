from flask import Flask, request, jsonify, render_template_string, send_from_directory, render_template, session, g, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from werkzeug.utils import secure_filename
from models import db, TarotBooking
import sqlite3
import base64
import sys
import io
import os
import re

app = Flask(__name__)
app.secret_key = "Meet@123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookings.db'
db.init_app(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True)
    active = db.Column(db.Boolean, default=False)
    profile_pic = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.png', mimetype='image/png'
    )

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form["password"]
        if password == "Meet@123":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AatmannByVarsha - Admin Login</title>
            <!-- SEO meta (admin pages are later disallowed in robots.txt) -->
            <meta name="description" content="Aatmann By Varsha">
            <meta name="robots" content="noindex, nofollow">
            <meta name="google-site-verification" content="PUT_CODE_HERE">
            <script src="https://cdn.tailwindcss.com"></script>
            <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png" sizes="32x32">
            <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png">
            <link rel="apple-touch-icon" href="{{ url_for('static', filename='favicon.png') }}?v=2">
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
            <style>
                .home-button {
                    position: fixed;
                    top: 0.5rem;
                    left: 0.5rem;
                    max-width: 3.5rem;
                    text-align: center;
                    margin-top: 10px;
                    margin-left: 10px;
                  }
            </style>
        </head>
        <body class="flex flex-col min-h-screen justify-center items-center bg-gray-100">
            <a href="{{ url_for('Home') }}" class="home-button">
              <img src="{{ url_for('static', filename='home.jpeg') }}" alt="Home Icon" title="Home">
            </a>
            <div class="bg-white shadow-lg rounded-2xl p-8 w-full max-w-md">
                <h2 class="text-2xl font-bold text-center mb-6">🔑 Admin Login</h2>

                <form method="POST" class="space-y-4">
                    <div>
                        <label class="block text-gray-700 mb-1">Password:</label>
                        <input type="password" name="password" required
                            class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    </div>

                    <button type="submit"
                        class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-lg transition">
                        Login
                    </button>
                </form>
            </div>

        </body>
        </html>
    ''')

@app.route("/admin_dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    bookings = TarotBooking.query.all()
    logged_in_users = User.query.filter_by(active=True).all()

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AatmannByVarsha - Admin Dashboard</title>
            <meta name="description" content="Aatmann By Varsha">
            <meta name="robots" content="noindex, nofollow">
            <script src="https://cdn.tailwindcss.com"></script>
            <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png" sizes="32x32">
            <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png">
            <link rel="apple-touch-icon" href="{{ url_for('static', filename='favicon.png') }}?v=2">
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
            <style>
                .home-button {
                    position: fixed;
                    top: 0.5rem;
                    left: 0.5rem;
                    max-width: 3.5rem;
                    text-align: center;
                    margin-top: 10px;
                    margin-left: 10px;
                  }
            </style>
        </head>
        <body class="flex flex-col min-h-screen bg-gray-100 p-8">
            <a href="{{ url_for('Home') }}" class="home-button">
              <img src="{{ url_for('static', filename='home.jpeg') }}" alt="Home Icon" title="Home">
            </a>
            <div class="bg-white shadow-lg rounded-2xl p-6 mt-6" style="position: relative; padding: 1.5rem; top: 2rem;">
                <h3 class="text-xl font-bold mb-4">👥 Active Users</h3>

                <div class="overflow-x-auto">
                    <table class="min-w-full table-auto border-collapse border border-gray-300">
                        <thead class="bg-purple-600 text-white">
                            <tr>
                                <th class="px-4 py-2 border border-gray-300">Name</th>
                                <th class="px-4 py-2 border border-gray-300">Phone</th>
                                <th class="px-4 py-2 border border-gray-300">Email</th>
                            </tr>
                        </thead>
                        <tbody id="userTable">
                            {% for u in logged_in_users %}
                            <tr class="hover:bg-gray-50 user-row {% if loop.index > 5 %}hidden{% endif %}">
                                <td class="px-4 py-2 border border-gray-300">{{ u.name }}</td>
                                <td class="px-4 py-2 border border-gray-300">{{ u.phone }}</td>
                                <td class="px-4 py-2 border border-gray-300">{{ u.email }}</td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="3" class="text-center text-gray-500 py-4">No users currently logged in</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                {% if logged_in_users|length > 5 %}
                <div class="text-center mt-4">
                    <button id="toggleButton"
                        class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition">
                        Show More
                    </button>
                </div>
                {% endif %}
            </div>


            <div class="flex justify-between items-center mb-6" style="position: relative; top: 3rem;">
                <h2 class="text-2xl font-bold">📖 Tarot Bookings Dashboard</h2>
                <a href="{{ url_for('Admin_logout') }}"
                   class="bg-red-500 hover:bg-red-600 text-white font-semibold px-4 py-2 rounded-lg transition">
                    Logout
                </a>
            </div>

            <div class="bg-white shadow-lg rounded-2xl p-6 overflow-x-auto" style="position: relative; padding: 1.5rem; top: 2.5rem;">
                <table class="min-w-full table-auto border-collapse border border-gray-300">
                    <thead class="bg-indigo-600 text-white">
                        <tr>
                            <th class="px-4 py-2 border border-gray-300">ID</th>
                            <th class="px-4 py-2 border border-gray-300">Name</th>
                            <th class="px-4 py-2 border border-gray-300">Phone</th>
                            <th class="px-4 py-2 border border-gray-300">Email</th>
                            <th class="px-4 py-2 border border-gray-300">Date</th>
                            <th class="px-4 py-2 border border-gray-300">Time</th>
                            <th class="px-4 py-2 border border-gray-300">Minutes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for b in bookings %}
                        <tr class="hover:bg-gray-50">
                            <td class="px-4 py-2 border border-gray-300">{{ b.id }}</td>
                            <td class="px-4 py-2 border border-gray-300">{{ b.name }}</td>
                            <td class="px-4 py-2 border border-gray-300">{{ b.phone }}</td>
                            <td class="px-4 py-2 border border-gray-300">{{ b.email }}</td>
                            <td class="px-4 py-2 border border-gray-300">{{ b.date }}</td>
                            <td class="px-4 py-2 border border-gray-300">{{ b.time }}</td>
                            <td class="px-4 py-2 border border-gray-300">{{ b.minutes }}</td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="7" class="text-center text-gray-500 py-4">No bookings yet</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            <script>
                document.addEventListener("DOMContentLoaded", function() {
                    const rows = document.querySelectorAll(".user-row");
                    const button = document.getElementById("toggleButton");
                    let expanded = false;

                    if (button) {
                        button.addEventListener("click", function() {
                            expanded = !expanded;
                            rows.forEach((row, index) => {
                                if (index >= 5) {
                                    row.classList.toggle("hidden", !expanded);
                                }
                            });
                            button.textContent = expanded ? "Show Less" : "Show More";
                        });
                    }
                });
            </script>
        </body>
        </html>
    ''', bookings=bookings, logged_in_users=logged_in_users)


@app.route("/Admin_logout")
def Admin_logout():
    if "user" in session:
        user_id = session["user"]["id"]
        user = User.query.get(user_id)
        if user:
            user.active = False
            db.session.commit()
        session.pop("user", None)
    return redirect(url_for("Home"))

@app.route('/')
def Home():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
          <title>Aatmann By Varsha - Tarot & Numerology</title>

          <!-- SEO meta tags (using your requested site name) -->
          <meta name="description" content="Aatmann By Varsha - Tarot & Numerology readings for clarity and guidance.">
          <meta name="robots" content="index, follow">
          <meta property="og:title" content="Aatmann By Varsha">
          <meta property="og:description" content="Aatmann By Varsha - Tarot & Numerology readings for clarity and guidance.">
          <meta property="og:url" content="https://aatmann-by-varsha-tarot-numerology.onrender.com/">
          <meta name="twitter:card" content="summary_large_image">
          <meta name="google-site-verification" content="UY6FzHRJXPd0P4vhPQ_kwUXPSUNx4KLln0Gkd6yQK5A" />

          <script src="https://cdn.tailwindcss.com"></script>
          <script src="https://unpkg.com/alpinejs" defer></script>
          <link rel="icon" href="/favicon.ico" type="image/x-icon">
          <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}" type="image/png" sizes="32x32">
          <link rel="apple-touch-icon" href="{{ url_for('static', filename='favicon.png') }}">
          <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
          <!-- Handwriting font for Numerology & Tarot headings -->
          <link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap" rel="stylesheet">
          <style>
            html, body {
              height: 100%;
              margin: 0;
              padding: 0;
              font-family: 'Inter', sans-serif;
              background: linear-gradient(to bottom right, #f3e8ff, #c7d2fe);
              background-attachment: fixed;
              background-size: cover;
            }
            body {
              display: flex;
              flex-direction: column;
              min-height: 100vh;
            }
            .button {
              cursor: pointer;
              background-color: #4f46e5;
              color: white;
              padding: 10px 20px;
              border-radius: 8px;
              text-decoration: none;
              transition: background 0.3s;
            }
            .button:hover { background-color: #4338ca; }
            .header-container {
              display: flex;
              justify-content: center;
              align-items: center;
              gap: 2rem;
              padding: 1rem;
            }
            .sidebar {
              padding-top: 50px; height: 100%; width: 0;
              position: fixed; background-color: #111; overflow-x: hidden;
              transition: 0.3s; z-index: 1001;
            }
            .sidebar a {
              padding: 10px 15px; text-decoration: none;
              font-size: 18px; color: #f1f1f1; display: block; transition: 0.3s;
            }
            .sidebar a:hover { background-color: #575757; }
            .sidebar .close-btn {
              position: absolute; top: 10px; right: 20px;
              font-size: 30px; cursor: pointer; color: #fff;
            }
            .overlay {
              position: fixed; top: 0; left: 0; width: 100%; height: 100%;
              background-color: rgba(0,0,0,0.5); z-index: 1000; display: none;
            }

            /* Phone */
            @media (max-width: 640px) {
              .heading-laptop { width: 12rem !important; }
              #daily-quote { margin-top: 0.5rem !important; font-size: 1rem !important; }
              .numerology-section h3, .tarot-section h3 { font-size: 1.8rem !important; }
              .numerology-section p, .tarot-section p { font-size: 0.95rem !important; margin-top: 2rem; }
              .numerology-section img, .tarot-section img { max-width: 90% !important; }
            }

            /* Tablet */
            @media (min-width: 641px) and (max-width: 1023px) {
              .heading-laptop { width: 28rem !important; }
              .tagline-section { margin-top: 2rem !important; }
              #daily-quote { font-size: 2.5rem !important; margin-top: 3rem !important; }
              .numerology-section p { margin-top: 3rem; }, .tarot-section p { margin-top: 2rem; }
              .numerology-section h3, .tarot-section h3 { font-size: 2.6rem !important; }
              .numerology-section img, .tarot-section img { max-width: 50% !important; }
            }

            /* Laptop */
            @media (min-width: 1024px) {
              .laptop-hide { display: none !important; }
              .heading-laptop { max-width: 21rem !important; margin-top: 1rem !important; }
              .tagline-section { margin-top: 2rem !important; }
              #daily-quote { margin-top: 1rem !important; font-size: 1rem !important; }
              .header-container { margin-top: 0 !important; }
              .numerology-section p { margin-top: 3rem; }, .tarot-section p { margin-top: 2rem; }
              .numerology-section h3, .tarot-section h3 { font-size: 3rem !important; }
            }

            /* Shared styles for numerology & tarot sections */
            .numerology-section, .tarot-section {
              margin-top: 1.5rem;
              padding: 1rem;
              background: rgba(255,255,255,0.06);
              border-radius: 12px;
              max-width: 900px;
              margin-left: auto;
              margin-right: auto;
              text-align: center;
              box-sizing: border-box;
            }
            .numerology-section h3, .tarot-section h3 {
              font-family: 'Dancing Script', cursive;
              font-weight: 700;
              color: #5b21b6;
              margin: 0;
              letter-spacing: 0.5px;
            }
            .numerology-section img, .tarot-section img {
              display: block; margin: 1rem auto;
              width: 100%; max-width: 480px;
              border-radius: 12px;
              box-shadow: 0 10px 25px rgba(0,0,0,0.12);
            }
            .numerology-section p, .tarot-section p {
              color: #2d3748;
              line-height: 1.6;
              font-size: 1.05rem;
            }
          </style>
        </head>
        <body class="flex flex-col min-h-screen" id="main">

          <!-- Avatar/Login -->
          <div class="fixed top-4 right-4 z-50">
            <div class="relative" x-data="{ open: false }">
              {% if session.get('user') %}
                <button @click="open = !open" class="focus:outline-none">
                  {% if session['user'].get('profile_pic') %}
                    <img src="{{ url_for('static', filename='uploads/' + session['user']['profile_pic']) }}"
                         class="w-10 h-10 rounded-full border-2 border-purple-500 shadow-md">
                  {% else %}
                    <div class="w-10 h-10 flex items-center justify-center rounded-full bg-purple-600 text-white text-xl font-bold border-2 border-purple-500 shadow-md">
                      {{ session['user']['name'][0] }}
                    </div>
                  {% endif %}
                </button>
                <div x-show="open" @click.outside="open = false"
                     class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border py-2 z-50">
                  <a href="{{ url_for('profile') }}" class="block px-4 py-2 text-gray-700 hover:bg-gray-100">Profile</a>
                  <a href="{{ url_for('Admin_logout') }}" class="block px-4 py-2 text-gray-700 hover:bg-gray-100">Logout</a>
                </div>
              {% else %}
                <a href="{{ url_for('user_login') }}" class="bg-indigo-600 text-white px-4 py-2 rounded-lg shadow-md hover:bg-indigo-700">Login</a>
              {% endif %}
            </div>
          </div>

          <!-- Sidebar -->
          <div id="mySidebar" class="sidebar">
            <span class="close-btn" onclick="closeMenu()">&times;</span>
            <a href="{{ url_for('Numerology') }}">Numerology</a>
            <a href="{{ url_for('Tarot') }}">Tarot Reading</a>
            <a href="/user_login">User Login</a>
            <a href="{{ url_for('About') }}">About Us</a>
          </div>
          <div id="overlay" class="overlay" onclick="closeMenu()"></div>

          <!-- Header -->
          <div class="header-container flex flex-col sm:flex-row justify-center items-center gap-4 sm:gap-8 mt-12">
            <img src="{{ url_for('static', filename='menu icon.png') }}" alt="Menu" title="Menu"
                 class="absolute top-4 left-4 w-10 h-10 sm:w-12 sm:h-12 cursor-pointer" onclick="openMenu()">
            <img src="{{ url_for('static', filename='heading.png') }}" alt="Heading"
                 class="mx-auto w-60 sm:w-64 md:w-80 lg:w-[30rem] heading-laptop">
            <a href="{{ url_for('Tarot') }}" class="button hidden sm:inline-block laptop-hide">Tarot Reading</a>
          </div>

          <!-- Daily Quote -->
          <div id="daily-quote" class="text-center mt-8 px-4 text-lg sm:text-xl md:text-2xl font-semibold text-gray-700">
            Quote Of Day: <span id="quote-text"></span>
          </div>

          <!-- Tagline -->
          <section class="tagline-section mt-8 px-6 text-center max-w-4xl mx-auto">
            <h2 class="text-2xl sm:text-3xl md:text-4xl font-extrabold text-gray-900 leading-snug">
              Skip the confusion and embrace absolute <span class="text-purple-600">CLARITY</span> with the power of <span class="text-purple-600">TAROT & NUMEROLOGY</span>!
            </h2>
            <p class="mt-4 text-gray-700 text-base sm:text-lg leading-relaxed">
              For seekers who are ready to define, refine, and align their life’s purpose by uncovering the hidden map of their <strong>past, present, and future</strong>.
            </p>
          </section>

          <!-- Numerology Section -->
          <section class="numerology-section" aria-labelledby="numerology-heading">
            <h3 id="numerology-heading">Numerology</h3>
            <img src="{{ url_for('static', filename='numerology.jpeg') }}" alt="Numerology" title="Numerology">
            <p><strong>Discover the energetic blueprint hidden in your numbers.</strong> Numerology decodes the vibration of your name, birthdate, and life events to reveal strengths, lessons, and timing cycles.</p>
            <p style="margin-top:1rem;">Whether you're curious about career timing, relationship compatibility, or personal purpose — numerology gives you clear, practical insights to navigate choices with confidence.</p>
          </section>

          <!-- Tarot Section -->
          <section class="tarot-section" aria-labelledby="tarot-heading">
            <h3 id="tarot-heading">Tarot Reading</h3>
            <img src="{{ url_for('static', filename='tarot.jpeg') }}" alt="Tarot" title="Tarot">
            <p><strong>Unveil the messages your soul is waiting to hear.</strong> Tarot provides symbolic guidance that mirrors your subconscious, helping you see choices, challenges, and opportunities with new clarity.</p>
            <p style="margin-top:1rem;">From love and career to spiritual growth, Tarot connects intuition with universal wisdom — guiding you toward decisions that align with your highest path.</p>
          </section>

          <div class="flex justify-center gap-4 flex-wrap">
            <a href="{{ url_for('Tarot') }}" class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg shadow-md font-semibold">Book a Tarot Reading</a>
          </div>
          <section class="mt-10 bg-white/80 rounded-2xl p-8 shadow-md">
              <div class="max-w-5xl mx-auto text-center">
                <h4 class="text-xl font-semibold text-purple-700">Why choose Numerology & Tarot with Varsha?</h4>

                <!-- Responsive grid: 2 cols on small, 3 cols on large -->
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-6 mt-6 text-left text-gray-700 text-sm sm:text-base">

                  <!-- Column 1 -->
                  <div class="space-y-4">
                    <div class="flex items-start gap-2"><span class="font-bold text-purple-600">1.</span> Years of experience combining numerology & tarot</div>
                    <div class="flex items-start gap-2"><span class="font-bold text-purple-600">2.</span> Compassionate, practical guidance you can use today</div>
                  </div>

                  <!-- Column 2 -->
                  <div class="space-y-4">
                    <div class="flex items-start gap-2"><span class="font-bold text-purple-600">3.</span> Secure, private online sessions</div>
                    <div class="flex items-start gap-2"><span class="font-bold text-purple-600">4.</span> Follow-up suggestions and action steps</div>
                  </div>

                  <!-- Column 3 -->
                  <div class="space-y-4">
                    <div class="flex items-start gap-2"><span class="font-bold text-purple-600">5.</span> Easy booking via WhatsApp & Zoom</div>
                    <div class="flex items-start gap-2"><span class="font-bold text-purple-600">6.</span> Personalized readings tailored to your life path</div>
                  </div>

                </div>
              </div>
          </section>

          <script>
            const spiritualQuotes = [
              "✨ Tarot whispers: Trust the journey, not just the destination.",
              "🔢 Numerology says: Your numbers guide you toward balance and clarity.",
              "💎 Crystals remind: Hold light within, and healing flows outward.",
              "📜 Akashic Records reveal: Your soul already knows the answers.",
              "🌙 Every card, number, and stone is a mirror of your higher self.",
              "🌌 The universe speaks softly — align your energy to hear it clearly.",
              "🔮 Your intuition is the strongest guide; trust its voice today."
            ];
            const today = new Date();
            const index = today.getDate() % spiritualQuotes.length;
            document.getElementById("quote-text").innerText = spiritualQuotes[index];

            function openMenu() {
              const sidebar = document.getElementById("mySidebar");
              const overlay = document.getElementById("overlay");
              const width = window.innerWidth;
              if (width <= 640) sidebar.style.width = "180px";
              else if (width <= 1023) sidebar.style.width = "200px";
              else sidebar.style.width = "250px";
              overlay.style.display = "block";
            }
            function closeMenu() {
              document.getElementById("mySidebar").style.width = "0";
              document.getElementById("overlay").style.display = "none";
            }
          </script>
        </body>
        </html>
    ''')

@app.route('/tarot')
def Tarot():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Aatmann By Varsha - Tarot</title>

      <!-- SEO meta using site name only -->
      <meta name="description" content="Aatmann By Varsha">
      <meta name="robots" content="index, follow">
      <meta property="og:title" content="Aatmann By Varsha">
      <meta property="og:description" content="Aatmann By Varsha">
      <meta property="og:url" content="https://aatmann-by-varsha-tarot-numerology.onrender.com/tarot">
      <meta name="twitter:card" content="summary_large_image">

      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
      <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png" sizes="32x32">
      <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png">
      <link rel="apple-touch-icon" href="{{ url_for('static', filename='favicon.png') }}?v=2">
      <script src="https://cdn.tailwindcss.com"></script>
      <style>
          html, body {
              height: 100%;
              margin: 0;
              padding: 0;
              font-family: 'Inter', sans-serif;
              background: linear-gradient(to bottom right, #f3e8ff, #c7d2fe);
              background-attachment: fixed;
              background-size: cover;
            }
            body {
              display: flex;
              flex-direction: column;
              min-height: 100vh;
            }
    </style>
    </head>
    <body class="min-h-screen text-gray-800">

      <a href="{{ url_for('Home') }}" class="fixed top-4 left-4 w-10 z-50">
        <img src="{{ url_for('static', filename='home.jpeg') }}" alt="Home" title="Home">
      </a>

      <header class="pt-12 pb-6 text-center">
        <h1 class="text-4xl font-extrabold text-purple-700">Tarot Readings</h1>
        <p class="mt-3 text-lg text-gray-600 max-w-2xl mx-auto">Find clarity, guidance, and healing through the wisdom of Tarot cards. Perfect for love, career, and life purpose. ✨</p>
      </header>

      <main class="px-4 pb-12 max-w-6xl mx-auto">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- 15 min -->
          <div class="bg-white shadow-md rounded-2xl p-6">
            <h3 class="text-xl font-semibold text-purple-600">15-Min Reading</h3>
            <p class="mt-2 text-gray-600">Quick insights on one question.</p>
            <div class="mt-4 flex justify-between items-center">
              <span class="font-bold text-purple-700">₹499</span>
              <a href="{{ url_for('book_tarot_detail', duration='15', source='tarot') }}" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold">Book Now</a>
            </div>
          </div>

          <!-- 30 min -->
          <div class="bg-white shadow-md rounded-2xl p-6">
            <h3 class="text-xl font-semibold text-purple-600">30-Min Reading</h3>
            <p class="mt-2 text-gray-600">Deeper guidance with multiple questions.</p>
            <div class="mt-4 flex justify-between items-center">
              <span class="font-bold text-purple-700">₹899</span>
              <a href="{{ url_for('book_tarot_detail', duration='30', source='tarot') }}" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold">Book Now</a>
            </div>
          </div>

          <!-- 60 min -->
          <div class="bg-white shadow-md rounded-2xl p-6">
            <h3 class="text-xl font-semibold text-purple-600">60-Min Reading</h3>
            <p class="mt-2 text-gray-600">In-depth reading with full spread.</p>
            <div class="mt-4 flex justify-between items-center">
              <span class="font-bold text-purple-700">₹1599</span>
              <a href="{{ url_for('book_tarot_detail', duration='60', source='tarot') }}" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold">Book Now</a>
            </div>
          </div>
        </div>

        <!-- Custom -->
        <div class="mt-8 bg-white shadow-md rounded-2xl p-6 max-w-lg mx-auto">
          <h3 class="text-xl font-semibold text-purple-600">Custom Time Slot</h3>
          <p class="mt-2 text-gray-600">Pick a time that suits your schedule for a personalized tarot reading.</p>
          <a href="{{ url_for('book_tarot_detail', duration='custom', source='tarot') }}" class="mt-4 inline-block bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold">Book Now</a>
        </div>
      </main>

      <footer class="py-6 text-center text-sm text-gray-600">
        AatmannByVarsha — Tarot guidance for insight and clarity.
      </footer>

    </body>
    </html>
    ''')

@app.route('/numerology')
def Numerology():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Aatmann By Varsha - Numerology</title>

      <!-- SEO meta using site name only -->
      <meta name="description" content="Aatmann By Varsha">
      <meta name="robots" content="index, follow">
      <meta property="og:title" content="Aatmann By Varsha">
      <meta property="og:description" content="Aatmann By Varsha">
      <meta property="og:url" content="https://aatmann-by-varsha-tarot-numerology.onrender.com/numerology">
      <meta name="twitter:card" content="summary_large_image">

      <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png" sizes="32x32">
      <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png">
      <link rel="apple-touch-icon" href="{{ url_for('static', filename='favicon.png') }}?v=2">
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-[#f3e8ff] to-[#c7d2fe] min-h-screen text-gray-800">

      <a href="{{ url_for('Home') }}" class="fixed top-4 left-4 w-10 z-50">
        <img src="{{ url_for('static', filename='home.jpeg') }}" alt="Home" title="Home">
      </a>

      <header class="pt-12 pb-6 text-center">
        <h1 class="text-4xl font-extrabold text-purple-700">Numerology Readings</h1>
        <p class="mt-3 text-lg text-gray-600 max-w-2xl mx-auto">Gain clarity, guidance, and spiritual insight through the wisdom of numbers. Whether about love, career, or destiny — numerology illuminates your path. ✨</p>
      </header>

      <main class="px-4 pb-12 max-w-6xl mx-auto">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <!-- 15 min -->
          <div class="bg-white shadow-md rounded-2xl p-6">
            <h3 class="text-xl font-semibold text-purple-600">15-Min Reading</h3>
            <p class="mt-2 text-gray-600">Quick numerology insights on one focus area.</p>
            <div class="mt-4 flex justify-between items-center">
              <span class="font-bold text-purple-700">₹499</span>
              <a href="{{ url_for('book_tarot_detail', duration='15', source='numerology') }}" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold">Book Now</a>
            </div>
          </div>

          <!-- 30 min -->
          <div class="bg-white shadow-md rounded-2xl p-6">
            <h3 class="text-xl font-semibold text-purple-600">30-Min Reading</h3>
            <p class="mt-2 text-gray-600">Deeper numerology reading with multiple questions.</p>
            <div class="mt-4 flex justify-between items-center">
              <span class="font-bold text-purple-700">₹899</span>
              <a href="{{ url_for('book_tarot_detail', duration='30', source='numerology') }}" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold">Book Now</a>
            </div>
          </div>

          <!-- 60 min -->
          <div class="bg-white shadow-md rounded-2xl p-6">
            <h3 class="text-xl font-semibold text-purple-600">60-Min Reading</h3>
            <p class="mt-2 text-gray-600">In-depth numerology session with full analysis.</p>
            <div class="mt-4 flex justify-between items-center">
              <span class="font-bold text-purple-700">₹1599</span>
              <a href="{{ url_for('book_tarot_detail', duration='60', source='numerology') }}" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold">Book Now</a>
            </div>
          </div>
        </div>

        <!-- Custom -->
        <div class="mt-8 bg-white shadow-md rounded-2xl p-6 max-w-lg mx-auto">
          <h3 class="text-xl font-semibold text-purple-600">Custom Time Slot</h3>
          <p class="mt-2 text-gray-600">Pick a time that suits you for a bespoke numerology reading.</p>
          <a href="{{ url_for('book_tarot_detail', duration='custom', source='numerology') }}" class="mt-4 inline-block bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-semibold">Book Now</a>
        </div>
      </main>

      <footer class="py-6 text-center text-sm text-gray-600">
        © 2025 AatmannByVarsha — Numerology guidance for life path clarity.
      </footer>

    </body>
    </html>
    ''')

@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if 1 == 1 :
        session.permanent = True
    else:
        session.permanent = False

    if request.method == "POST":
        email = request.form["email"]
        phone = request.form["phone"]
        name = request.form["name"]

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(name=name, phone=phone, email=email, active=True)
            db.session.add(user)
            db.session.commit()
        else:
            user.name = name
            user.phone = phone
            user.active = True
            db.session.commit()

        session["user"] = {
            "id": user.id,
            "name": user.name,
            "phone": user.phone,
            "email": user.email,
            "profile_pic": user.profile_pic
        }

        return redirect(url_for("Home"))
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Aatmann By Varsha - User Login</title>

            <!-- SEO meta using site name only -->
            <meta name="description" content="Aatmann By Varsha">
            <meta name="robots" content="index, follow">
            <meta property="og:title" content="Aatmann By Varsha">
            <meta property="og:description" content="Aatmann By Varsha">
            <meta property="og:url" content="https://aatmann-by-varsha-tarot-numerology.onrender.com/user_login">
            <meta name="twitter:card" content="summary_large_image">

            <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png" sizes="32x32">
            <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png">
            <link rel="apple-touch-icon" href="{{ url_for('static', filename='favicon.png') }}?v=2">
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                body {
                    font-family: 'Inter', sans-serif;
                    background: linear-gradient(to bottom right, #f3e8ff, #c7d2fe);
                }
                .home-button {
                    position: fixed;
                    top: 0.5rem;
                    left: 0.5rem;
                    width: 3rem;
                    z-index: 50;
                }
                .phone-row {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
                .phone-row select {
                    flex: 0 0 6rem;
                    background: #f9fafb;
                    padding: 0.5rem;
                    border: 1px solid #d1d5db;
                    border-radius: 0.5rem;
                }
                .phone-row input {
                    flex: 1;
                }
                /* Mobile tweaks */
                @media (max-width: 480px) {
                    .phone-row select {
                        flex: 0 0 5rem;
                        font-size: 0.85rem;
                        padding: 0.5rem;
                    }
                    .phone-row input {
                        font-size: 0.9rem;
                        padding: 0.5rem;
                    }
                }
            </style>
        </head>
        <body class="flex flex-col min-h-screen justify-center items-center">
            <a href="{{ url_for('Home') }}" class="home-button">
              <img src="{{ url_for('static', filename='home.jpeg') }}" alt="Home Icon" title="Home">
            </a>

            <div class="bg-white shadow-lg rounded-2xl p-8 w-full max-w-md login-box">
                <h2 class="text-2xl font-bold text-center mb-6">👤 User Login</h2>

                <form method="POST" class="space-y-4" autocomplete="off">
                    <!-- Full Name -->
                    <div>
                        <label class="block text-gray-700 mb-1">Full Name:</label>
                        <input placeholder="Real Name"
                               type="text"
                               name="name"
                               required
                               autocomplete="new-password"
                               class="w-full border border-gray-300 rounded-lg px-4 py-2">
                    </div>

                    <!-- Country Code + Phone -->
                    <div>
                        <label class="block text-gray-700 mb-1">Phone:</label>
                        <div class="phone-row">
                            <select name="country_code" id="countryCode" autocomplete="new-password">
                              <option value="+91" data-min="10" data-max="12">🇮🇳 +91</option>
                              <option value="+1"  data-min="10" data-max="12">🇺🇸 +1</option>
                              <option value="+44" data-min="10" data-max="12">🇬🇧 +44</option>
                              <option value="+61" data-min="9"  data-max="11">🇦🇺 +61</option>
                            </select>
                            <input type="tel"
                                   id="phone"
                                   name="phone"
                                   placeholder="Phone Number"
                                   inputmode="numeric"
                                   autocomplete="new-password"
                                   required
                                   class="border border-gray-300 rounded-lg px-4 py-2">
                        </div>
                    </div>

                    <!-- Email -->
                    <div>
                        <label class="block text-gray-700 mb-1">Email:</label>
                        <input type="email"
                               placeholder="Email Id"
                               name="email"
                               required
                               autocomplete="new-password"
                               class="w-full border border-gray-300 rounded-lg px-4 py-2">
                    </div>

                    <!-- Button -->
                    <button type="submit"
                        class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-lg transition">
                        Login
                    </button>
                </form>
            </div>
            <script>
              const phoneInput = document.getElementById("phone");
              const countryCode = document.getElementById("countryCode");

              function updatePhoneValidation() {
                const selected = countryCode.options[countryCode.selectedIndex];
                const min = parseInt(selected.getAttribute("data-min"));
                const max = parseInt(selected.getAttribute("data-max"));

                phoneInput.setAttribute("minlength", min);
                phoneInput.setAttribute("maxlength", max);

                // live validation
                phoneInput.addEventListener("input", function () {
                  this.setCustomValidity("");
                  const val = this.value.trim();
                  if (!/^\d+$/.test(val)) {
                    this.setCustomValidity("Only digits allowed");
                  } else if (val.length < min || val.length > max) {
                    this.setCustomValidity(`Phone number must be ${min}-${max} digits long`);
                  }
                });
              }

              updatePhoneValidation();
              countryCode.addEventListener("change", updatePhoneValidation);

              document.querySelector("form").addEventListener("submit", function (e) {
                phoneInput.setCustomValidity(""); // clear old error
                const selected = countryCode.options[countryCode.selectedIndex];
                const min = parseInt(selected.getAttribute("data-min"));
                const max = parseInt(selected.getAttribute("data-max"));
                const val = phoneInput.value.trim();

                if (!/^\d+$/.test(val) || val.length < min || val.length > max) {
                  e.preventDefault(); // stop submit
                  phoneInput.setCustomValidity(`Please give a valid Phone Number (${min}-${max} digits)`);
                  phoneInput.reportValidity();
                }
              });
            </script>
        </body>
        </html>
    ''')

@app.route("/akashic-records")
def akashic_records():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Aatmann By Varsha - Akashic Records (Under Development)</title>

      <!-- 🚫 Hide from Google until ready -->
      <meta name="robots" content="noindex, nofollow">

      <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}" type="image/png" sizes="32x32">
      <link rel="apple-touch-icon" href="{{ url_for('static', filename='favicon.png') }}">
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
      <link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap" rel="stylesheet">
      <script src="https://cdn.tailwindcss.com"></script>

      <style>
        body {
          font-family: 'Inter', sans-serif;
          background: linear-gradient(to bottom right, #f3e8ff, #c7d2fe);
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
        }
        h1 {
          font-family: 'Dancing Script', cursive;
          font-size: 2.5rem;
          color: #5b21b6;
          margin-bottom: 1rem;
        }
        p {
          color: #374151;
          font-size: 1.2rem;
          max-width: 600px;
          margin: 0 auto;
        }
      </style>
    </head>
    <body>
      <a href="{{ url_for('Home') }}" class="fixed top-4 left-4 w-10">
        <img src="{{ url_for('static', filename='home.jpeg') }}" alt="Home">
      </a>

      <h1>🚧 Akashic Records Page</h1>
      <p>This page is under development. Soon you’ll explore deep soul wisdom and past life insights here. ✨</p>
    </body>
    </html>
    """)


@app.route("/crystals")
def crystals():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Aatmann By Varsha - Crystals (Under Development)</title>

      <!-- 🚫 Hide from Google until ready -->
      <meta name="robots" content="noindex, nofollow">

      <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}" type="image/png" sizes="32x32">
      <link rel="apple-touch-icon" href="{{ url_for('static', filename='favicon.png') }}">
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
      <link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap" rel="stylesheet">
      <script src="https://cdn.tailwindcss.com"></script>

      <style>
        body {
          font-family: 'Inter', sans-serif;
          background: linear-gradient(to bottom right, #f3e8ff, #c7d2fe);
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
        }
        h1 {
          font-family: 'Dancing Script', cursive;
          font-size: 2.5rem;
          color: #5b21b6;
          margin-bottom: 1rem;
        }
        p {
          color: #374151;
          font-size: 1.2rem;
          max-width: 600px;
          margin: 0 auto;
        }
      </style>
    </head>
    <body>
      <a href="{{ url_for('Home') }}" class="fixed top-4 left-4 w-10">
        <img src="{{ url_for('static', filename='home.jpeg') }}" alt="Home">
      </a>

      <h1>🚧 Crystals Page</h1>
      <p>This page is under construction. Soon you’ll discover healing and energy-balancing with crystals here. 🌌</p>
    </body>
    </html>
    """)

@app.route('/about us')
def About():
    return render_template_string('''
      <!DOCTYPE html>
      <html lang="en">
      <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Aatmann By Varsha - About Us</title>
          <meta name="description" content="Aatmann By Varsha">
          <meta name="robots" content="index, follow">
          <meta property="og:title" content="Aatmann By Varsha">
          <meta property="og:description" content="Aatmann By Varsha">
          <meta property="og:url" content="https://aatmann-by-varsha-tarot-numerology.onrender.com/about">
          <meta name="twitter:card" content="summary_large_image">

          <script src="https://cdn.tailwindcss.com"></script>
          <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png" sizes="32x32">
          <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png">
          <link rel="apple-touch-icon" href="{{ url_for('static', filename='favicon.png') }}?v=2">
          <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
          <style>
              html, body {
                height: 100%;
                margin: 0;
                padding: 0;
                font-family: 'Inter', sans-serif;
                background: linear-gradient(to bottom right, #f3e8ff, #c7d2fe);
                background-attachment: fixed;   /* ✅ Prevent gradient from restarting */
                background-size: cover;
              }
              body {
                display: flex;
                flex-direction: column;
                min-height: 100vh;
              }

              /* --- Top Bar --- */
              .top-bar {
                width: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 1rem 1rem;
                position: relative;
              }
              .home-button {
                position: absolute;
                left: 1rem;
                top: 0.5rem;
                width: 3rem;
                height: auto;
              }
              .page-heading {
                font-size: 2.5rem;
                font-weight: 800;
                color: #111827;
              }

              /* --- Content Card --- */
              .content {
                margin-top: 2rem;
                padding: 3rem;
                font-size: 1rem;
                font-weight: 400;
                text-align: center;
                color: #111827;
                background: white;
                border-radius: 1.5rem;
                box-shadow: 0 8px 22px rgba(0,0,0,0.15);
                max-width: 900px;
                width: 90%;
                margin-left: auto;
                margin-right: auto;
                margin-bottom: 2rem;
              }

              .icons {
                width: 24px;
                height: 24px;
                vertical-align: middle;
                border-radius: 6px;
                display: inline-block;
              }

              /* 📱 Mobile */
              @media (max-width: 640px) {
                .page-heading {
                  font-size: 1.8rem;
                }
                .content {
                  padding: 1.5rem;
                  font-size: 0.95rem;
                }
              }

              /* 📱 Tablets */
              @media (min-width: 641px) and (max-width: 1023px) {
                .page-heading {
                  font-size: 2.2rem;
                }
                .content {
                  padding: 2rem;
                  font-size: 1.05rem;
                  max-width: 700px;
                }
              }

              /* 💻 Laptop/Desktop */
              @media (min-width: 1024px) and (max-width: 1365px) {
                .page-heading {
                  font-size: 2.6rem;
                }
                .content {
                  padding: 3rem 4rem;
                  font-size: 1.1rem;
                }
              }

              /* 📱 iPad Pro / Large Tablets */
              @media (min-width: 1024px) and (max-width: 1366px) and (orientation: portrait),
                     (min-width: 1366px) and (max-width: 1366px) {
                .page-heading {
                  font-size: 3rem;   /* ✅ larger heading for iPad Pro */
                }
                .content {
                  max-width: 950px;
                  padding: 3.5rem;
                  font-size: 1.15rem;
                }
              }

              /* 🖥 Desktop Large Screens */
              @media (min-width: 1367px) {
                .page-heading {
                  font-size: 2.8rem;
                }
                .content {
                  max-width: 1000px;
                }
              }
          </style>
      </head>
      <body class="flex flex-col min-h-screen">

        <!-- Top section with Home + Heading -->
        <div class="top-bar">
          <a href="{{ url_for('Home') }}" class="home-button">
            <img src="{{ url_for('static', filename='home.jpeg') }}" alt="Home Icon" title="Home">
          </a>
          <h1 class="page-heading">About Us</h1>
        </div>

        <!-- Content -->
        <div class="content">
          <p class="text-lg leading-relaxed">
            <strong>Unlock Your Destiny:</strong> A Journey Through <b>Psychic, Akashic, Numerology, and Tarot Readings.</b>
          </p>

          <p class="mt-6 leading-relaxed">
            Are you seeking clarity, guidance, and a deeper understanding of your life's path?
            We offer profound insights through a unique blend of ancient wisdom and intuitive abilities.
          </p>

          <p class="mt-6 leading-relaxed">
            Tap into the unseen energies around you to gain foresight, understand current challenges,
            and illuminate your future possibilities.
          </p>

          <p class="mt-6 leading-relaxed">
            Journey into the <b>Akashic Records</b> — the energetic library of all universal events,
            thoughts, and emotions — to uncover past life influences, karmic patterns,
            and your soul's higher purpose.
          </p>

          <h2 class="text-2xl font-semibold mt-10 mb-4">✨ Personal Consultation</h2>
          <p class="leading-relaxed">
            For Personal Consultation, contact us:
          </p>
          <p class="mt-2">
            <img src="{{ url_for('static', filename='whatsapp icon.jpeg') }}" alt="Whatsapp Icon" title="Whatsapp" class="icons">
            <b>WhatsApp:</b> <a href="https://wa.me/919354653343" class="text-blue-600 underline">+91 93546 53343</a>
          </p>
          <p class="mt-2">
            <img src="{{ url_for('static', filename='instagram icon.jpeg') }}" alt="Instagram Icon" title="Instagram" class="icons">
            <b>Instagram:</b> <a href="https://www.instagram.com/aatmannbyvarsha" class="text-blue-600 underline">@aatmannbyvarsha</a>
          </p>
        </div>
      </body>
      </html>
    ''')

@app.route("/book-tarot/<duration>", methods=["GET", "POST"])
def book_tarot_detail(duration):
    # Normalize duration_text
    if duration == "15":
        duration_text = "15 minutes"
    elif duration == "30":
        duration_text = "30 minutes"
    elif duration == "60":
        duration_text = "60 minutes"
    else:
        duration_text = "custom"

    # Get caller/source so the same booking page can show contextual heading/message
    # expected values: 'tarot', 'numerology', or others (defaults to 'tarot')
    source = request.args.get("source", "tarot")

    # Back link: return user to the page they came from
    if source == "numerology":
        back_url = url_for("Numerology")
        page_area_name = "Numerology"
    elif source == "home":
        back_url = url_for("Home")
        page_area_name = "Home"
    else:
        back_url = url_for("Tarot")
        page_area_name = "Tarot"

    # Title / header for the booking card (customized)
    if duration_text == "custom":
        header_text = f"Book Custom {page_area_name} Reading"
    else:
        header_text = f"Book {duration_text} {page_area_name} Reading"

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{{ header_text }}</title>

      <!-- SEO meta using site name only -->
      <meta name="description" content="Aatmann By Varsha">
      <meta name="robots" content="index, follow">
      <meta property="og:title" content="Aatmann By Varsha">
      <meta property="og:description" content="Aatmann By Varsha">
      <meta property="og:url" content="https://aatmann-by-varsha-tarot-numerology.onrender.com/book-tarot">
      <meta name="twitter:card" content="summary_large_image">

      <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png" sizes="32x32">
      <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png">
      <link rel="apple-touch-icon" href="{{ url_for('static', filename='favicon.png') }}?v=2">
      <style>
        body { margin:0; font-family:'Poppins',sans-serif; min-height:100vh;
               background: linear-gradient(to bottom right,#f3e8ff,#c7d2fe);
               display:flex; justify-content:center; align-items:center; padding:1rem; }
        .home-button { position: fixed; left:0.5rem; top:0.5rem; }
        .home-button img { width:3rem; height:auto; }
        .card { background:rgba(255,255,255,0.95); padding:2rem; border-radius:1rem; width:100%; max-width:560px; box-shadow:0 10px 25px rgba(0,0,0,0.15); }
        h1 { color:#4c1d95; text-align:center; margin-bottom:1rem; }
        .input-group { margin-bottom:1rem; text-align:left; }
        label{ font-weight:600; color:#6d28d9; display:block; margin-bottom:6px; }
        input, select { width:100%; padding:10px; border-radius:8px; border:1px solid #d1d5db; }
        button { margin-top:10px; width:100%; padding:12px; background:linear-gradient(135deg,#8b5cf6,#6366f1); color:white; border:none; border-radius:8px; font-weight:600; cursor:pointer; }
        .small-note { margin-top:0.75rem; font-size:0.9rem; color:#374151; text-align:center; }
      </style>
    </head>
    <body>
      <!-- back button goes to the page user came from -->
      <a href="{{ back_url }}" class="home-button" title="Back to {{ page_area_name }}">
        <img src="{{ url_for('static', filename='home.jpeg') }}" alt="Back">
      </a>

      <div class="card">
        <h1>{{ header_text }}</h1>
        <form id="bookingForm">
          <div class="input-group"><label>👤 Full Name</label><input type="text" id="name" required></div>
          <div class="input-group"><label>📞 Phone</label><input type="tel" id="phone" required></div>
          <div class="input-group"><label>✉️ Email</label><input type="email" id="email" required></div>
          <div class="input-group"><label>📅 Day</label><input type="date" id="date" required></div>
          <div class="input-group"><label>⏰ Time</label><input type="time" id="time" required></div>

          {% if duration_text == 'custom' %}
          <div class="input-group"><label>⏳ Duration</label>
            <select id="duration" required>
              <option value="15 minutes">15 minutes</option>
              <option value="30 minutes">30 minutes</option>
              <option value="45 minutes">45 minutes</option>
              <option value="60 minutes">1 hour</option>
              <option value="90 minutes">1 hour 30 minutes</option>
            </select>
          </div>
          {% endif %}

          <button type="submit">✨ Confirm Booking</button>
        </form>

        <div class="small-note">You are booking from the <strong>{{ page_area_name }}</strong> page. After clicking confirm the WhatsApp chat will open.</div>
      </div>

      <script>
        document.getElementById("bookingForm").addEventListener("submit", function(e){
          e.preventDefault();
          let name = document.getElementById("name").value.trim();
          let phone = document.getElementById("phone").value.trim();
          let email = document.getElementById("email").value.trim();
          let date = document.getElementById("date").value;
          let time = document.getElementById("time").value;
          let duration = "{{ duration_text }}";
          {% raw %}
          if (duration === "custom") {
            duration = document.getElementById("duration").value;
          }
          {% endraw %}

          if (!name || !phone || !email || !date || !time) {
            alert("Please fill all required fields.");
            return;
          }

          // include the source page name in the whatsapp message so you know context
          let sourceName = "{{ page_area_name }}";
          let message = `Hi, I am ${name}. I'd like to book a ${duration} ${sourceName} session on ${date} at ${time}. Please confirm my session time. Contact: ${phone} / ${email}`;
          window.open(`https://wa.me/919354653343?text=${encodeURIComponent(message)}`, "_blank");
        });
      </script>
    </body>
    </html>
    """, duration_text=duration_text, header_text=header_text, back_url=back_url, page_area_name=page_area_name)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect(url_for("user_login"))

    # Get the user from DB
    user_data = session["user"]
    user = User.query.filter_by(email=user_data["email"]).first()

    if not user:
        return redirect(url_for("user_login"))

    # Handle profile picture upload
    if request.method == "POST":
        file = request.files.get("profile_pic")
        if file:
            filename = secure_filename(file.filename)
            os.makedirs("static/uploads", exist_ok=True)
            filepath = os.path.join("static/uploads", filename)
            file.save(filepath)
            user.profile_pic = filename
            db.session.commit()

            session["user"] = {
                "id": user.id,
                "name": user.name,
                "phone": user.phone,
                "email": user.email,
                "profile_pic": user.profile_pic
            }

            return redirect(url_for("profile"))

    profile_pic = user.profile_pic if user.profile_pic else None

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aatmann By Varsha - Profile</title>
        <!-- ✅ This makes media queries work on phones -->

        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <!-- SEO meta using site name only -->
        <meta name="description" content="Aatmann By Varsha">
        <meta name="robots" content="index, follow">
        <meta property="og:title" content="Aatmann By Varsha">
        <meta property="og:description" content="Aatmann By Varsha">
        <meta property="og:url" content="https://aatmann-by-varsha-tarot-numerology.onrender.com/profile">
        <meta name="twitter:card" content="summary_large_image">

        <link rel="icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png" sizes="32x32">
        <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.png') }}?v=2" type="image/png">
        <link rel="apple-touch-icon" href="{{ url_for('static', filename='favicon.png') }}?v=2">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
              html, body {
                height: 100%;
                margin: 0;
                padding: 0;
                font-family: 'Inter', sans-serif;
                background-color: #ffffff;
              }
              body {
                display: flex;
                flex-direction: column;
                min-height: 100vh;
              }
              .home-button {
                position: fixed;
                max-width: 3.5rem;
                height: auto;
                text-align: center;
                margin-top: 10px;
                margin-left: 10px;
              }

              /* Mobile-first: take full width, then limit on larger screens */
              .profile-card {
                background: white;
                border-radius: 1rem;
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                padding: 2rem;
                width: 80%;
                max-width: 20rem;
                text-align: center;
                box-sizing: border-box;
              }

              /* Make it feel bigger on phones (<= 640px) */
              @media (max-width: 640px) {
                .profile-card {
                  padding: 2.5rem 1.5rem;
                  max-width: 20rem;
                }
                .profile-card h2 { font-size: 2rem; }
                .profile-card p { font-size: 1.15rem; }
                .avatar-size { width: 7rem; height: 7rem; font-size: 2rem; }
              }

              /* Desktop/tablet: cap width like before */
              @media (min-width: 641px) {
                .profile-card {
                  max-width: 28rem;     /* ✅ previous desktop size */
                }
              }
        </style>
    </head>
    <body class="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-purple-100 to-indigo-200">

        <!-- Home Button -->
        <a href="{{ url_for('Home') }}" class="home-button" style="position: fixed; top: 1rem; left: 1rem; width: 3.5rem;">
          <img src="{{ url_for('static', filename='home.jpeg') }}" alt="Home Icon" title="Home">
        </a>

        <!-- Profile Card -->
        <div class="profile-card">
            <h2 class="text-2xl font-bold mb-6">👤 My Profile</h2>

            {% if profile_pic %}
                <img src="{{ url_for('static', filename='uploads/' + profile_pic) }}"
                     class="avatar-size rounded-full mx-auto mb-4 shadow-lg" style="width:6rem;height:6rem;">
            {% else %}
                <div class="avatar-size flex items-center justify-center rounded-full bg-purple-600 text-white text-3xl font-bold mx-auto mb-4 shadow-lg"
                     style="width:6rem; height:6rem;">
                    {{ user.name[0] if user and user.name else 'U' }}
                </div>
            {% endif %}

            <p><b>Name:</b> {{ user.name }}</p>
            <p><b>Email:</b> {{ user.email }}</p>
            <p><b>Phone:</b> {{ user.phone }}</p>

            <!-- Upload Button (Browse + Auto Submit) -->
            <form method="POST" enctype="multipart/form-data" class="mt-4">
                <input type="file" name="profile_pic" id="fileInput" class="hidden" accept="image/*">
                <button type="button" onclick="document.getElementById('fileInput').click()"
                        class="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700">
                    Upload Profile Image
                </button>
                <button type="submit" class="hidden" id="uploadBtn"></button>
            </form>

            <!-- Logout -->
            <a href="{{ url_for('user_logout') }}"
               class="mt-6 inline-block bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600">
               Logout
            </a>
        </div>

        <script>
            // Auto-submit after selecting file
            document.getElementById("fileInput").addEventListener("change", function() {
                document.getElementById("uploadBtn").click();
            });
        </script>
    </body>
    </html>
    """, user=user, profile_pic=profile_pic)

@app.route("/robots.txt")
def robots_txt():
    content = (
        "User-agent: *\n"
        "Allow: /favicon.ico\n"
        "Allow: /static/favicon.png\n"
        "Disallow: /user_login\n"
        "Disallow: /admin_login\n"
        "Disallow: /admin_dashboard\n"
        "Disallow: /Admin_logout\n"
        "Disallow: /akashic-records\n"
        "Disallow: /crystals\n"
        "Allow: /\n"
        "Sitemap: https://www.aatmannbyvarsha.com/sitemap.xml\n"
    )
    return content, 200, {"Content-Type": "text/plain"}

@app.route("/sitemap.xml")
def sitemap_xml():
    sitemap = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://aatmann-by-varsha-tarot-numerology.onrender.com/</loc></url>
      <url><loc>https://aatmann-by-varsha-tarot-numerology.onrender.com/tarot</loc></url>
      <url><loc>https://aatmann-by-varsha-tarot-numerology.onrender.com/numerology</loc></url>
      <url><loc>https://aatmann-by-varsha-tarot-numerology.onrender.com/about us</loc></url>
    </urlset>
    """
    return sitemap, 200, {"Content-Type": "application/xml"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

