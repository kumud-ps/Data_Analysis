# AI Email Agent

A cost-free AI-powered email automation agent that reads Gmail emails, generates intelligent contextual responses using local LLMs, and automatically replies to and deletes processed emails. Built to run entirely on free cloud hosting with zero infrastructure costs.

## 🌟 Features

- **Automated Email Processing**: Continuously monitors Gmail inbox via IMAP
- **AI-Powered Responses**: Smart contextual replies using Ollama with Llama 3.2 1B model
- **Intelligent Classification**: Automatically categorizes emails (business, personal, support, etc.)
- **Content Safety**: Built-in content filtering and security checks
- **Flexible Scheduling**: Configurable email checking intervals and quiet hours
- **Rate Limiting**: Prevents Gmail API abuse with intelligent rate limiting
- **Comprehensive Logging**: Structured logging with audit trails
- **Web Dashboard**: Beautiful Streamlit-based control interface
- **REST API**: Full HTTP API for monitoring and control
- **Zero Cost**: Runs on free hosting platforms (Render, Railway)

## 🏗️ Architecture

### Core Components

1. **Email Processing Engine** (`src/email/`)
   - `reader.py`: Gmail IMAP integration for reading emails
   - `sender.py`: Gmail SMTP integration for sending replies
   - `parser.py`: Email content parsing and analysis
   - `processor.py`: Main email processing logic

2. **AI Response Generator** (`src/ai/`)
   - `ollama_client.py`: Ollama LLM integration
   - `prompt_templates.py`: Context-aware response templates
   - `response_generator.py`: Smart reply generation

3. **Automation Controller** (`src/scheduler/`)
   - `email_monitor.py`: Scheduled email monitoring with APScheduler

4. **Configuration & Utilities** (`src/config/`, `src/utils/`)
   - `settings.py`: Comprehensive configuration management
   - `logger.py`: Structured logging with audit trails
   - `exceptions.py`: Custom exception handling

5. **API Layer** (`src/main.py`)
   - FastAPI application with comprehensive endpoints

6. **Web Dashboard** (`dashboard.py`)
   - Streamlit-based user interface for control and monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Gmail account with App Password enabled
- Ollama service (local or remote)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-email-agent
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Gmail Configuration
EMAIL_GMAIL_USERNAME=your-email@gmail.com
EMAIL_GMAIL_APP_PASSWORD=your-16-character-app-password

# AI Configuration
AI_OLLAMA_BASE_URL=http://localhost:11434
AI_MODEL_NAME=llama3.2:1b

# Processing Configuration
PROCESSING_CHECK_INTERVAL_MINUTES=5
PROCESSING_DELETE_PROCESSED=true
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the model
ollama pull llama3.2:1b
```

### 5. Run the Application

#### Option 1: With Dashboard (Recommended)

```bash
# Start both API and Streamlit dashboard
python run_dashboard.py
```

This will start:
- **API Server**: http://localhost:8000
- **Web Dashboard**: http://localhost:8502

#### Option 2: API Only

```bash
# Development mode
python src/main.py

# Or with uvicorn directly
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Option 3: Dashboard Only

```bash
# Start dashboard (API must be running separately)
streamlit run dashboard.py --server.port=8501
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Start all services (includes dashboard)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

This will start:
- **API Server**: http://localhost:8000
- **Web Dashboard**: http://localhost:8502
- **Ollama Service**: http://localhost:11434

### Using Docker

```bash
# Build image
docker build -t ai-email-agent .

# Run container
docker run -p 8000:8000 --env-file .env ai-email-agent
```

## ☁️ Cloud Deployment

### Deploy to Render (Free Tier)

1. **Push to GitHub**: Ensure your code is on GitHub
2. **Create Render Account**: Sign up at [render.com](https://render.com)
3. **Connect Repository**: Connect your GitHub repository
4. **Configure Environment Variables**: Set up credentials in Render dashboard
5. **Deploy**: Use the provided `render.yaml` configuration

**Important Notes for Free Hosting:**
- External Ollama service required (VPS or Railway)
- Service spin-up delays after 15 minutes of inactivity
- No persistent storage (configuration in environment variables)

### Deploy to Railway

Similar to Render, using Railway's free tier with Docker deployment.

## 📚 User Interfaces

Once running, you have several ways to control and monitor your AI Email Agent:

### 🎛️ Web Dashboard (Recommended)

Visit **http://localhost:8502** for a beautiful, user-friendly interface that includes:

- **System Status Overview**: Real-time health monitoring
- **Control Panel**: Start/stop monitoring, process emails manually
- **Statistics Dashboard**: Visual charts and processing metrics
- **Recent Activity**: Detailed processing history
- **Configuration Viewer**: Current settings overview
- **Auto-refresh**: Keep data up-to-date automatically

### 🤖 Telegram Bot (Mobile Control)

Control your AI Email Agent from anywhere using Telegram! Perfect for mobile access and quick actions.

**Setup:**
```bash
# Run setup assistant for detailed instructions
python telegram_setup.py

# After setup, add to .env:
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_USER_ID=your_user_id_here  # Optional
```

**Start Telegram Bot:**
```bash
# Make sure API server is running first
python src/main.py &

# Then start Telegram bot
python telegram_bot.py
```

**Available Commands:**
- `/start` - Welcome message with quick actions
- `/status` - Current monitoring status
- `/health` - System health check
- `/start_monitoring [minutes]` - Start email monitoring
- `/stop_monitoring` - Stop email monitoring
- `/process_emails [limit]` - Process emails manually
- `/stats` - View processing statistics

**Features:**
- ✅ Inline buttons for quick actions
- 📊 Real-time status updates
- 🔄 Manual email processing
- 📈 Statistics and health monitoring
- 📱 Mobile-friendly interface

### 🔌 API Documentation

For programmatic control:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### Email Processing
- `POST /emails/process` - Manually trigger email processing
- `POST /emails/process-background` - Process emails in background
- `POST /emails/check-immediate` - Schedule immediate email check

#### Monitoring Control
- `POST /monitoring/start` - Start automated monitoring
- `POST /monitoring/stop` - Stop automated monitoring
- `POST /monitoring/update-interval` - Update check interval

#### Status & Health
- `GET /health` - Comprehensive health check
- `GET /status` - Current monitoring status
- `GET /stats` - Processing statistics
- `POST /stats/reset` - Reset statistics

#### Configuration
- `GET /config` - View current configuration (sans secrets)

## ⚙️ Configuration

### Gmail Setup

1. **Enable 2-Step Verification**: Required for App Passwords
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this 16-character password in `EMAIL_GMAIL_APP_PASSWORD`

### Processing Settings

```env
# Email processing behavior
PROCESSING_AUTO_REPLY_ENABLED=true      # Enable automatic replies
PROCESSING_DELETE_PROCESSED=true       # Delete processed emails
PROCESSING_MAX_EMAILS_PER_BATCH=10     # Max emails per processing run
PROCESSING_CHECK_INTERVAL_MINUTES=5    # Email checking frequency

# Quiet hours (no responses during these times)
PROCESSING_QUIET_HOURS_START=22:00
PROCESSING_QUIET_HOURS_END=08:00

# Sender filtering (optional)
# PROCESSING_ALLOWED_SENDERS=user1@domain.com,user2@domain.com
# PROCESSING_BLOCKED_SENDERS=spam@domain.com
```

### Security Settings

```env
SECURITY_ENABLE_CONTENT_FILTER=true    # Block inappropriate content
SECURITY_MAX_ATTACHMENT_SIZE_MB=5      # Max attachment size
SECURITY_LOG_LEVEL=INFO               # Logging verbosity
SECURITY_ENABLE_AUDIT_LOG=true        # Enable audit logging
```

### AI Settings

```env
AI_OLLAMA_BASE_URL=http://localhost:11434  # Ollama API URL
AI_MODEL_NAME=llama3.2:1b                  # Model to use
AI_TEMPERATURE=0.7                         # Response creativity (0-1)
AI_MAX_TOKENS=500                          # Max response length
AI_TIMEOUT=30                             # Request timeout (seconds)
```

## 📊 Monitoring & Logging

### Logging Structure

The application uses structured logging with multiple output formats:

- **Console**: Colored, human-readable logs
- **File**: JSON-structured logs in `logs/` directory
- **Audit**: Separate audit log for security events

### Metrics Tracked

- Total emails processed
- Successful responses sent
- Failed responses
- Skipped emails
- Processing errors
- Response times

### Health Monitoring

Built-in health checks monitor:
- Gmail connectivity (IMAP/SMTP)
- Ollama service availability
- Memory and CPU usage
- Recent error rates

## 🔒 Security Features

### Content Filtering
- Blocks inappropriate content
- Attachment size limits
- Sender whitelist/blacklist
- Suspicious link detection

### Rate Limiting
- Prevents Gmail API abuse
- Per-recipient rate limits
- Configurable cooldown periods

### Secure Credential Handling
- Environment variable storage
- No hardcoded secrets
- Encrypted communication (TLS)

## 🛠️ Development

### Project Structure

```
ai-email-agent/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── email/                  # Email processing
│   │   ├── reader.py          # IMAP email reading
│   │   ├── sender.py          # SMTP email sending
│   │   ├── parser.py          # Content parsing
│   │   └── processor.py       # Main processing logic
│   ├── ai/                    # AI components
│   │   ├── ollama_client.py   # Ollama integration
│   │   ├── prompt_templates.py # Response templates
│   │   └── response_generator.py # Response generation
│   ├── scheduler/             # Automation
│   │   └── email_monitor.py   # Scheduled monitoring
│   ├── config/                # Configuration
│   │   └── settings.py        # Settings management
│   └── utils/                 # Utilities
│       ├── logger.py          # Logging setup
│       └── exceptions.py      # Custom exceptions
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── .env.example
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Format code
black src/
isort src/

# Type checking
mypy src/

# Linting
flake8 src/
```

## 🔧 Troubleshooting

### Common Issues

**Gmail Authentication Failed**
- Ensure 2-Step Verification is enabled
- Generate a new App Password
- Check email format (username@gmail.com)

**Ollama Connection Failed**
- Verify Ollama is running: `ollama list`
- Check model availability: `ollama pull llama3.2:1b`
- Verify URL configuration

**Memory Issues on Free Hosting**
- Use smaller model (llama3.2:1b)
- Reduce batch sizes
- Implement regular cleanup

**Rate Limiting by Gmail**
- Increase check intervals
- Reduce batch sizes
- Monitor error rates

### Debug Mode

Enable debug logging:

```env
API_DEBUG=true
SECURITY_LOG_LEVEL=DEBUG
```

## 📈 Performance & Limitations

### Free Hosting Constraints

- **Render**: 750 instance hours/month, spin-up delays
- **No persistent storage**: Configuration in environment variables
- **Memory limits**: ~512MB-1GB typical
- **CPU limits**: Shared CPU resources

### Expected Performance

- **Email check**: 5-30 seconds
- **AI response generation**: 2-10 seconds
- **Total processing**: 10-40 seconds per email
- **Memory usage**: 200-500MB (including Ollama)

### Optimization Tips

- Use Llama 3.2 1B model for faster responses
- Implement email batching
- Set appropriate quiet hours
- Monitor and adjust rate limits

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Submit Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the API docs at `/docs`
- **Health Check**: Use `/health` endpoint for diagnostics

## 🗺️ Roadmap

### Upcoming Features

- [ ] Multiple email provider support (Outlook, Yahoo)
- [ ] Advanced AI features (sentiment analysis, priority scoring)
- [x] Web dashboard for monitoring
- [ ] Mobile app companion
- [ ] Team collaboration features
- [ ] CRM integrations
- [ ] Calendar integration
- [ ] Attachment processing

### Enhancements

- [ ] OAuth2 authentication support
- [ ] End-to-end encryption
- [ ] GDPR compliance features
- [ ] Advanced threat detection
- [ ] Performance analytics
- [ ] Custom model training

---

**Built with ❤️ for cost-free email automation**