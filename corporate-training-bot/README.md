# Corporate Training Bot

A comprehensive Telegram bot for corporate training with knowledge base management, testing system, and administrative controls.

## Features

- **User Authentication**: Role-based access control (admin/regular users)
- **Knowledge Base**: Categorized product information with multimedia support
- **Testing System**: Interactive quizzes with scoring and progress tracking
- **Search Functionality**: Product search capabilities
- **Admin Panel**: Complete content management system
- **Database Integration**: SQLite for development, PostgreSQL for production

## Environment Variables

Set these environment variables for deployment:

```
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=340877389
ENVIRONMENT=production
DATABASE_URL=your_postgresql_url (optional, uses SQLite if not set)
PORT=10000
RENDER_EXTERNAL_URL=https://your-app.onrender.com
```

## Deployment on Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following configuration:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Environment Variables**: Add the variables listed above

## Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables in a `.env` file
4. Run: `python main.py`

## Project Structure

```
corporate-training-bot/
├── handlers/           # Bot command handlers
│   ├── __init__.py
│   ├── start.py       # Start command and main menu
│   ├── admin.py       # Admin panel functionality
│   ├── knowledge.py   # Knowledge base browsing
│   ├── testing.py     # Test taking system
│   └── search.py      # Product search
├── middleware/         # Custom middleware
│   └── auth.py        # Authentication middleware
├── utils/             # Utility modules
│   ├── keyboards.py   # Inline keyboard builders
│   └── helpers.py     # Helper functions
├── config.py          # Configuration settings
├── database.py        # Database operations
├── models.py          # SQLAlchemy models
├── main.py           # Application entry point
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Bot Commands

- `/start` - Start the bot and show main menu

## Admin Features

- Category management (create, edit, delete)
- Product management with file uploads
- Test question creation and management
- System statistics

## User Features

- Browse knowledge base by categories
- Search for products
- Take interactive tests
- View test results and progress

## Database Schema

- **Users**: User information and admin status
- **Categories**: Product categories
- **Products**: Product information with optional files
- **TestQuestions**: Quiz questions for products
- **TestResults**: User test scores and history

## License

This project is licensed under the MIT License.