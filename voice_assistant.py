"""
Voice Assistant Program
A Python-based virtual assistant that responds to voice commands
for performing various tasks like web search, weather, emails, etc.
"""

# Import required libraries
import speech_recognition as sr  # For speech recognition
import pyttsx3  # For text-to-speech
import datetime  # For time/date functions
import webbrowser  # For opening websites
import os  # For environment variables
import wikipedia  # For Wikipedia searches
import pyjokes  # For telling jokes
import requests  # For API requests
import json  # For JSON handling
import smtplib  # For sending emails
from email.message import EmailMessage  # For email formatting
import wolframalpha  # For computational knowledge
import subprocess  # For system commands
from dotenv import load_dotenv  # For secure API key management

# Load environment variables from .env file
load_dotenv()

# Initialize components
recognizer = sr.Recognizer()  # Speech recognition object
engine = pyttsx3.init()  # Text-to-speech engine
wolfram_client = wolframalpha.Client(os.getenv('WOLFRAM_APP_ID'))  # WolframAlpha client

# Voice configuration
voices = engine.getProperty('voices')  # Get available voices
engine.setProperty('voice', voices[0].id)  # Set voice (0=male, 1=female)
engine.setProperty('rate', 180)  # Set speech rate (words per minute)

def speak(text):
    """
    Convert text to speech and speak it aloud
    Args:
        text (str): The text to be spoken
    """
    engine.say(text)
    engine.runAndWait()

def take_command():
    """
    Listen for voice commands with fallback to keyboard input
    Returns:
        str: The recognized command in lowercase
    """
    try:
        with sr.Microphone() as source:
            print("\nListening... (speak now)")
            # Adjust for ambient noise with longer duration
            recognizer.adjust_for_ambient_noise(source, duration=2)
            # Set longer pause threshold
            recognizer.pause_threshold = 2.5
            # Lower sensitivity for quieter voices
            recognizer.energy_threshold = 3000
            
            # Listen with extended timeouts
            audio = recognizer.listen(
                source, 
                timeout=10,  # Wait 10 seconds for speech to start
                phrase_time_limit=8  # Allow 8 seconds of continuous speech
            )
            
            # Recognize speech using Google's API
            query = recognizer.recognize_google(audio).lower()
            print(f"Detected: {query}")
            return query
            
    except sr.WaitTimeoutError:
        print("\nNo speech detected for 10 seconds")
        speak("I didn't hear you. Please type your command instead.")
        return input("\nType your command here > ").lower()
    except sr.UnknownValueError:
        print("\nSpeech not recognized")
        speak("I didn't understand. Please type your command.")
        return input("\nType your command here > ").lower()
    except Exception as e:
        print(f"\nError: {e}")
        speak("There was a technical issue. Please type your command.")
        return input("\nType your command here > ").lower()    

def greet():
    """Greet the user based on current time of day"""
    hour = datetime.datetime.now().hour
    if 6 <= hour < 12:
        speak("Good morning! How can I assist you today?")
    elif 12 <= hour < 18:
        speak("Good afternoon! What can I do for you?")
    else:
        speak("Good evening! How may I help you?")

def get_time():
    """Speak the current time in 12-hour format"""
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"It's {current_time}")

def get_date():
    """Speak the current date in full format"""
    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today is {current_date}")

def search_wikipedia(query):
    """
    Search Wikipedia and speak a 2-sentence summary
    Args:
        query (str): The search term with "wikipedia" removed
    """
    try:
        speak("Searching Wikipedia...")
        query = query.replace("wikipedia", "").strip()
        results = wikipedia.summary(query, sentences=2, auto_suggest=False)
        speak(f"According to Wikipedia: {results}")
    except wikipedia.DisambiguationError as e:
        speak("Multiple matches found. Please be more specific.")
    except Exception:
        speak("Sorry, I couldn't find that on Wikipedia.")

def open_website(url_name):
    """
    Open predefined websites in default browser
    Args:
        url_name (str): Name of website to open
    """
    sites = {
        'youtube': 'https://youtube.com',
        'google': 'https://google.com',
        'github': 'https://github.com',
        'stackoverflow': 'https://stackoverflow.com',
        'instagram': 'https://instagram.com',
        'facebook': 'https://facebook.com',
        'twitter': 'https://twitter.com',
        'whatsapp': 'https://www.whatsapp.com'
    }
    
    if url_name in sites:
        webbrowser.open(sites[url_name])
        speak(f"Opening {url_name}")
    else:
        speak("Website not configured")

def send_email(receiver, subject, content):
    """
    Send email via Gmail SMTP
    Args:
        receiver (str): Recipient email address
        subject (str): Email subject
        content (str): Email body content
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Validate email format
        if not validate_email(receiver):
            speak("Invalid email format. Please include @ and domain like example.com")
            return False

        # Create email message
        email = EmailMessage()
        email['From'] = os.getenv('EMAIL_USER')
        email['To'] = receiver
        email['Subject'] = subject
        email.set_content(content)

        # Send via Gmail SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()  # Enable TLS encryption
            
            try:
                smtp.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
            except smtplib.SMTPAuthenticationError:
                speak("Email login failed. Check your credentials.")
                return False
                
            smtp.send_message(email)
        
        speak(f"Email to {receiver} sent successfully!")
        return True

    except smtplib.SMTPRecipientsRefused:
        speak("The recipient email was rejected. Please check the address.")
    except smtplib.SMTPException as e:
        speak(f"Email server error: {get_smtp_error(e)}")
    except Exception as e:
        speak("An unexpected error occurred")
        print(f"Email Error: {type(e).__name__}: {e}")
    
    return False

def validate_email(email):
    """
    Basic email format validation
    Args:
        email (str): Email address to validate
    Returns:
        bool: True if valid format, False otherwise
    """
    return ('@' in email and 
            '.' in email.split('@')[-1] and 
            len(email.split('@')[0]) > 0)

def get_smtp_error(e):
    """
    Convert SMTP error codes to user-friendly messages
    Args:
        e (Exception): SMTP exception object
    Returns:
        str: Human-readable error message
    """
    if hasattr(e, 'smtp_code'):
        codes = {
            '550': 'Recipient mailbox not found',
            '553': 'Invalid email address',
            '554': 'Transaction failed'
        }
        return codes.get(str(e.smtp_code), str(e))
    return str(e)

def get_weather(city):
    """
    Fetch and speak weather information for a city
    Args:
        city (str): City name to get weather for
    """
    try:
        api_key = os.getenv('WEATHER_API_KEY')
        base_url = "https://api.openweathermap.org/data/2.5/weather?"
        complete_url = f"{base_url}q={city}&appid={api_key}&units=metric"
        
        response = requests.get(complete_url)
        data = response.json()
        
        if data["cod"] == 200:
            main = data["main"]
            weather = data["weather"][0]
            speak(f"Weather in {city}: {weather['description']}. Temperature: {main['temp']}°C, "
                  f"Humidity: {main['humidity']}%")
        else:
            speak("City not found")
    except Exception as e:
        speak("Weather service unavailable")
        print(f"Weather API error: {e}")

def tell_joke():
    """Tell a random programming joke"""
    speak(pyjokes.get_joke())

def compute_answer(query):
    """
    Answer computational/factual questions using WolframAlpha
    Args:
        query (str): The question/calculation to compute
    """
    try:
        res = wolfram_client.query(query)
        answer = next(res.results).text
        speak(answer)
    except StopIteration:
        speak("I couldn't compute that")
    except Exception as e:
        speak("Computation service unavailable")
        print(f"WolframAlpha error: {e}")

def execute_command(query):
    """
    Process and execute voice commands
    Args:
        query (str): The voice command to execute
    Returns:
        bool: False if exit command given, True otherwise
    """
    query = query.lower()
    
    if not query:
        return True
    
    # Command routing
    if "time" in query:
        get_time()
    elif "date" in query:
        get_date()
    elif "wikipedia" in query:
        search_wikipedia(query)
    elif "open " in query:
        site = query.split("open ")[1].split()[0]
        open_website(site)
    elif "weather" in query:
        speak("Which city?")
        city = take_command()
        if city:
            get_weather(city)
    elif "joke" in query:
        tell_joke()
    elif "email" in query:
        try:
            speak("Recipient's email?")
            receiver = take_command()
            speak("Email subject?")
            subject = take_command()
            speak("Message content?")
            content = take_command()
            send_email(receiver, subject, content)
        except Exception:
            speak("Email cancelled")
    elif "calculate" in query or "what is" in query or "who is" in query:
        compute_answer(query)
    elif "exit" in query or "bye" in query:
        speak("Goodbye! Have a great day.")
        return False
    else:
        speak("Command not recognized")
    
    return True

# Main program loop
if __name__ == "__main__":
    greet()  # Initial greeting
    running = True
    
    while running:
        query = take_command()  # Get user input
        running = execute_command(query)  # Process command