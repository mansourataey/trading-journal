# Trading Journal

A professional local web-based trading journal built with FastAPI, SQLite, and HTML/CSS for traders who want full control over their data.

## Features

- Secure first-time account setup
- User login and logout
- Local SQLite database
- Add, edit, and delete trades
- Upload and manage trade screenshots
- Trade history with search and filters
- Calendar view with TP, SL, BE, and Manual Close indicators
- Dashboard analytics
- Strategy performance tracking
- Mistake analytics
- Recent trades overview
- Excel and ZIP export
- Full backup and restore
- Local-first data storage
- Modern user interface

## System Requirements

- Windows 10 or Windows 11
- Python 3.11 or newer

## Installation

1. Download or clone this repository.

2. Open the project folder.

3. Double-click the file:

run.bat

4. The application will automatically create the virtual environment, install dependencies, and start the server.

5. Open your browser and go to:

http://127.0.0.1:8000

## First Setup

On first launch, create your account by entering:

- Full Name
- Username or Email
- Profile Photo
- Password

## Dashboard

The dashboard shows:

- Total Trades
- Win Rate
- Total Profit or Loss
- Average Risk Reward
- Total Wins
- Total Losses
- Best Trade
- Worst Trade
- Most Traded Symbol
- Biggest Mistake
- Strategy Performance
- Mistake Analytics
- Recent Trades

## Trade Management

Each trade can include:

- Date
- Symbol
- Direction
- Entry Price
- Stop Loss
- Take Profit
- Lot Size
- Risk Amount
- Result
- Profit or Loss
- Strategy
- Mistake
- Emotion
- Notes
- Multiple chart screenshots

## Calendar

The calendar view allows traders to review trades by date.

Color indicators:

- TP: Green
- SL: Red
- BE: Gray
- Manual Close: Orange

## Export

The export feature generates a ZIP file containing:

- Excel file with all trade details
- Screenshot folder
- Clickable screenshot links inside Excel

## Backup and Restore

The backup feature creates a full backup ZIP containing:

- SQLite database
- Uploaded screenshots

The restore feature allows the user to restore previous journal data from a valid backup ZIP file.

## Local Data Storage

Database location:

app/data/journal.db

Uploaded screenshots location:

app/static/uploads/

Export files location:

app/static/exports/

Backup files location:

app/static/backups/

No cloud storage is used. All data stays on the user's computer.

## Dependencies

- FastAPI
- Uvicorn
- Jinja2
- SQLAlchemy
- python-multipart
- openpyxl
- itsdangerous

## Developer

Developed by Mohammad Mansour Ataey

GitHub: https://github.com/mansourataey
Email: mansour@ataey.com

## Version

v1.0.0

## License

Personal and educational use unless otherwise specified.