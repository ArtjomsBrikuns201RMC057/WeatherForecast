import tkinter as tk
from tkinter import ttk
import requests
from tkinter import messagebox
from datetime import datetime
from PIL import Image, ImageTk
import sqlite3


API_KEY = '6bd5b87a56f44d62928131730240906'
DB_NAME = 'cities.db'

def fetch_cities(search_term=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if search_term:
        cursor.execute('SELECT city_name FROM cities WHERE city_name LIKE ?', ('%' + search_term + '%',))
    else:
        cursor.execute('SELECT city_name FROM cities')
    cities = [row[0] for row in cursor.fetchall()]
    conn.close()
    return cities

current_city_data = None
details_visible = False

def kelvin_to_celsius(kelvin):
    return kelvin - 273.15

def fetch_weather(city):
    url = f'http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}&aqi=no'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        messagebox.showerror("Error", "Failed to retrieve data " + str(response.status_code))
        return None

def fetch_forecast(city):
    url = f'http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={city}&days=7&aqi=no&alerts=no'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        messagebox.showerror("Error", f"Failed to retrieve data: {response.status_code}")
        return None

def format_weather(data, forecast_data):
    location = data['location']
    current = data['current']
    forecast_days = forecast_data['forecast']['forecastday']

    current_weather = {
        "city": location['name'] + ', ' + location['country'],
        "icon": current['condition']['icon'],
        "date": datetime.strptime(location['localtime'], '%Y-%m-%d %H:%M').strftime("%A, %d/%m"),
        "temp": current['temp_c'],
        "feels_like": current['feelslike_c'],
        "temp_min": forecast_days[0]['day']['mintemp_c'],
        "temp_max": forecast_days[0]['day']['maxtemp_c'],
        "condition": current['condition']['text']
    }

    forecast = []
    for i, day in enumerate(forecast_days[1:], start=1):
        if i == 1:
            date = 'Tomorrow, ' + datetime.strptime(day['date'], '%Y-%m-%d').strftime("%d %B").lstrip('0')
        else:
            date = datetime.strptime(day['date'], '%Y-%m-%d').strftime("%A, %d %B").lstrip('0')
        temp_min = day['day']['mintemp_c']
        temp_max = day['day']['maxtemp_c']
        icon = day['day']['condition']['icon']
        forecast.append({
            "date": date,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "icon": icon
        })

    return current_weather, forecast

def show_weather(city):
    global current_city_data, details_visible
    data = fetch_weather(city)
    forecast_data = fetch_forecast(city)
    if data and forecast_data:
        current_weather, forecast = format_weather(data, forecast_data)
        current_city_data = data
        update_weather_display(current_weather)
        if details_visible:
            show_detailed_weather()
        else:
            show_forecast(forecast)

def update_weather_display(current):
    city_label.config(text=current["city"])
    date_label.config(text=current["date"])
    temp_label.config(text=f"{current['temp']:.0f}°C")
    feels_like_label.config(text=f"Feels like {current['feels_like']:.0f}°C")
    temp_min_max_label.config(text=f"Max: {current['temp_max']:.0f}°C / Min: {current['temp_min']:.0f}°C")

    weather_icon_image = Image.open(requests.get(f'http:{current["icon"]}', stream=True).raw)
    weather_icon_image = weather_icon_image.resize((50, 50), Image.LANCZOS)
    weather_icon_photo = ImageTk.PhotoImage(weather_icon_image)
    weather_icon_label.config(image=weather_icon_photo)
    weather_icon_label.image = weather_icon_photo

def show_forecast(forecast):
    global details_visible
    details_visible = False
    details_button.config(text="Show Details")

    for widget in forecast_frame.winfo_children():
        widget.destroy()

    wrapper_frame = tk.Frame(forecast_frame, bg='#2E2E2E')
    wrapper_frame.pack(anchor='center', expand=True)

    for i, day in enumerate(forecast):
        frame = tk.Frame(wrapper_frame, bg='#2E2E2E')
        frame.pack(fill='x', pady=2)

        date = tk.Label(frame, text=day["date"], font=("Helvetica", 12), bg='#2E2E2E', fg='white')
        date.pack(side='left', padx=10)

        icon_image = Image.open(requests.get(f'http:{day["icon"]}', stream=True).raw)
        icon_image = icon_image.resize((50, 50), Image.LANCZOS)
        icon_photo = ImageTk.PhotoImage(icon_image)
        icon = tk.Label(frame, image=icon_photo, bg='#2E2E2E', fg='white')
        icon.image = icon_photo
        icon.pack(side='left', padx=20)

        temp = tk.Label(frame, text=f"{day['temp_max']:.0f}°C / {day['temp_min']:.0f}°C", font=("Helvetica", 12), bg='#2E2E2E', fg='white')
        temp.pack(side='left', padx=10)

def show_detailed_weather():
    global current_city_data, details_visible
    if not current_city_data:
        return

    if details_visible:
        details_visible = False
        show_forecast(format_weather(current_city_data, fetch_forecast(current_city_data['location']['name']))[1])
        return

    details_visible = True
    details_button.config(text="Show Forecast")

    for widget in forecast_frame.winfo_children():
        widget.destroy()

    details_frame = tk.Frame(forecast_frame, bg='#2E2E2E')
    details_frame.pack(fill='both', expand=True, pady=10)

    location = current_city_data['location']
    current = current_city_data['current']

    details_text = (
        f"City: {location['name']}, {location['country']}\n"
        f"Local Time: {location['localtime']}\n"
        f"Temperature: {current['temp_c']}°C\n"
        f"Condition: {current['condition']['text']}\n"
        f"Wind Speed: {current['wind_kph']} kph\n"
        f"Wind Direction: {current['wind_dir']}\n"
        f"Pressure: {current['pressure_mb']} mb\n"
        f"Humidity: {current['humidity']}%\n"
        f"Cloud: {current['cloud']}%\n"
        f"Feels Like: {current['feelslike_c']}°C\n"
        f"UV Index: {current['uv']}\n"
        f"Visibility: {current['vis_km']} km\n"
    )

    details_label = tk.Label(details_frame, text=details_text, font=("Helvetica", 16), bg='#2E2E2E', fg='white')
    details_label.pack(pady=10)

def search_cities(event):
    search_term = search_entry.get().lower()
    listbox.delete(0, tk.END)
    cities = fetch_cities(search_term)
    for city in cities:
        listbox.insert(tk.END, city)

def on_search_select(event):
    selected_city = listbox.get(listbox.curselection())
    show_weather(selected_city)

def init_search_results():
    cities = fetch_cities()
    for city in cities:
        listbox.insert(tk.END, city)

root = tk.Tk()
root.title("Weather Forecast")
root.geometry("1000x800")

sidebar_frame = tk.Frame(root, bg='#2E2E2E', bd=2, relief='ridge')
sidebar_frame.place(relx=0, rely=0, relwidth=0.2, relheight=1)

search_entry = tk.Entry(sidebar_frame, bg='#4E4E4E', fg='white', font=("Helvetica", 16), width=30)
search_entry.pack(fill='x', pady=5)
search_entry.bind('<KeyRelease>', search_cities)

listbox = tk.Listbox(sidebar_frame, bg='grey', fg='white', font=("Helvetica", 14))
listbox.pack(fill='both', expand=True, pady=5)
listbox.bind('<<ListboxSelect>>', on_search_select)

init_search_results()

weather_frame = tk.Frame(root, bg='#2E2E2E', bd=2)
weather_frame.place(relx=0.2, rely=0, relwidth=0.8, relheight=1)

city_label = tk.Label(weather_frame, text="", font=("Helvetica", 24), bg='#2E2E2E', fg='white')
city_label.pack(pady=5)

date_label = tk.Label(weather_frame, text="", font=("Helvetica", 16), bg='#2E2E2E', fg='white')
date_label.pack(pady=5)

weather_icon_label = tk.Label(weather_frame, bg='#2E2E2E')
weather_icon_label.pack(pady=5)

temp_label = tk.Label(weather_frame, text="", font=("Helvetica", 48), bg='#2E2E2E', fg='white')
temp_label.pack(pady=5)

feels_like_label = tk.Label(weather_frame, text="", font=("Helvetica", 16), bg='#2E2E2E', fg='white')
feels_like_label.pack(pady=5)

temp_min_max_label = tk.Label(weather_frame, text="", font=("Helvetica", 16), bg='#2E2E2E', fg='white')
temp_min_max_label.pack(pady=5)

forecast_frame = tk.Frame(weather_frame, bg='#2E2E2E')
forecast_frame.pack(fill='both', expand=True, pady=10)

details_button = tk.Button(weather_frame, text="Show Details", command=show_detailed_weather, bg='#4E4E4E', fg='white')
details_button.pack(pady=10)

show_weather("Riga")

root.mainloop()
