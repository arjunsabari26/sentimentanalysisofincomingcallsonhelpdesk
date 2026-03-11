# AI Helpdesk Call Sentiment Analyzer

A full-stack professional web application to modern helpdesks. Built with Flask, SQLite, TextBlob, and SpeechRecognition.

## Features
- **Authentication**: secure agent and admin logins.
- **Audio Analysis**: uploads `.wav` call recordings and converts them to text.
- **Sentiment Detection**: evaluates real-time caller sentiment (Positive, Neutral, Negative).
- **Dashboard**: robust analytics with Chart.js charts and metrics.
- **Admin**: role-based control panel and CSV exports.

## How to Setup

1. **Install Requirements:**
   Make sure you have Python 3 installed. Then, run:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: if TextBlob noun parsing raises errors, you may need to run `python -m textblob.download_corpora`.*

2. **Run Application:**
   ```bash
   python app.py
   ```
   The application will run on `http://127.0.0.1:5000/`.


## Password Reset & Email Setup

The application uses `Flask-Mail` to send actual emails for password resets and customer support responses.

### Local Development (Console Fallback)
By default, if no credentials are provided, the system will log the reset links and email content to the **server console (terminal)**. This allows you to test the flow without entering real email credentials.

### Real Email Configuration
To send real emails (e.g., using Gmail), you must set the following **environment variables**:

- `EMAIL_USER`: Your Gmail address (e.g., `example@gmail.com`)
- `EMAIL_PASS`: Your Gmail **App Password** (Required for Gmail accounts with 2FA).

**How to set on Windows:**
```powershell
$env:EMAIL_USER = "your-email@gmail.com"
$env:EMAIL_PASS = "your-app-password"
python app.py
```

**How to set on macOS/Linux:**
```bash
export EMAIL_USER="your-email@gmail.com"
export EMAIL_PASS="your-app-password"
python app.py
```

*Note: For Gmail, you can generate an App Password in your [Google Account Settings](https://myaccount.google.com/apppasswords).*

## Uploading Test Calls
Since this uses Google's free Web Speech API, please upload **.wav** audio files containing English speech for best results. When testing the app, try clear audio to simulate an actual helpdesk interaction.
