# API Sculptor

A powerful web-based tool for  bundling, building, and splitting OpenAPI specifications. API Sculptor provides an intuitive interface for working with modular OpenAPI files, allowing you to select specific endpoints and generate custom API documentation bundles.

The underlying technology is `Redocly CLI`, the tool is useful if you are not good at not remembering the commands to perform thes functions.  

## 🚀 Features

- **Interactive API Explorer**: Browse your OpenAPI specification with a clean, organized interface.
- **Selective Bundling**: Choose specific endpoints and generate custom API bundles.
- **Split Monolithic Specs**: Break down large OpenAPI files into modular components.
- **Modern UI**: Clean, responsive interface built with modern web technologies.

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 16+** (for Redocly CLI)
- **npm** or **yarn** (for Redocly CLI installation)

## 🛠️ Installation

### 1. Clone the Repository.
```bash
git clone <your-repo-url>
cd API_Sculptor
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Redocly CLI
Choose one of the following options:

**Global Installation (Recommended)**
```bash
npm install -g @redocly/cli
```

## 🎯 Quick Start

### 1. Prepare Your OpenAPI Specification
Place your main OpenAPI specification file as `openapi.yaml` in the project root, or update the `ROOT_SPEC_FILE` in `config.py` to point to your specification file.

### 2. Start the Application
```bash
python app.py
```

### 3. Open Your Browser
Navigate to `http://127.0.0.1:5000` to access the API Sculptor interface.

## 📁 Project Structure

```
API_Sculptor/
├── app.py                 # Main application entry point
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── openapi.yaml         # Main OpenAPI specification file
├── templates/
│   └── index.html       # Web interface template
├── src/
│   ├── __init__.py
│   ├── routes.py        # Flask routes and API endpoints
│   ├── openapi_utils.py # OpenAPI file utilities
│   └── redocly_cli.py   # Redocly CLI wrapper
├── components/          # OpenAPI components (schemas, examples, etc.)
├── paths/              # OpenAPI path definitions
└── README.md           # This file
```

## 🔧 Configuration

### Main Configuration (`config.py`)
- `ROOT_SPEC_FILE`: Path to your main OpenAPI specification
- `TEMP_SPEC_FILE`: Temporary file used during bundling process

### OpenAPI Specification Structure
API Sculptor works best with modular OpenAPI specifications that use `$ref` to external files:

```yaml
openapi: 3.0.4
info:
  title: Your API
  version: 1.0.0
paths:
  /users:
    $ref: components/schemas/userrequest
  /orders:
    $ref: components/schemas/orderrequest
components:
  schemas:
    User:
      $ref: components/schemas/User
```

## 🌐 API Endpoints

### Web Interface
- `GET /` - Main application interface

### API Endpoints
- `GET /api/paths` - Get all available API paths grouped by tags
- `POST /api/bundle` - Generate a bundled OpenAPI specification
- `POST /api/split` - Split a monolithic OpenAPI file into modular components
- `POST /api/diff` - Compare two OpenAPI specifications

## 📖 Usage Guide

### 1. Exploring Your API
1. Run the application using and go to the URL. 
2. The interface will automatically load your OpenAPI specification
3. Browse endpoints organized by tags(_This will only work, if you have tagged your endpoints in the OpenAPI file.)
4. Use the search functionality to find specific endpoints

### 2. Creating Custom Bundles
1. Select the endpoints you want to include in your bundle
2. Click "**Generate and Download Bundle**"
3. Choose a filename for your bundled specification
4. The system will generate a clean, bundled OpenAPI file

### 3. Splitting Monolithic Specifications
1. Use the "**Splitter**" feature
2. Upload your monolithic OpenAPI file
3. The system will break it down into modular components
4. Restart the server to see the new structure


## 🐛 Troubleshooting

### Common Issues

**"Redocly CLI not found" Error**
```bash
# Install Redocly CLI globally
npm install -g @redocly/cli

# Or verify Node.js is installed for npx fallback
node --version
```

**"File not found" Errors**
- Ensure your `openapi.yaml` file exists in the project root
- Check that referenced path files exist in the `paths/` directory
- Verify component references in the `components/` directory

**Windows File Access Errors**
- The application automatically handles Windows file locking issues
- If you encounter permission errors, restart the application

**Port Already in Use**
```bash
# Use a different port
python app.py --port 5001

# Or kill the process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F
```

## 🔧 Development

### Running in Development Mode
```bash
# Enable debug mode
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows
python app.py
```

### Code Style
The project uses Black for code formatting:
```bash
black src/ app.py config.py
```

### Testing
```bash
pytest
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Uses [Redocly CLI](https://redocly.com/docs/cli/) for OpenAPI processing
- Inspired by modern API documentation tools

## 📞 Support

If you encounter any issues or have questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Search existing [Issues](../../issues)
3. Create a new issue with detailed information about your problem

---

**Happy API Sculpting! 🎨**
