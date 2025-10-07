# GitHub Pages Deployment Guide

## 🚀 **Static Frontend Deployment**

The RE Market Tool now supports GitHub Pages deployment with a hybrid architecture:

- **Static Mode**: GitHub Pages (read-only functionality)
- **Dynamic Mode**: Flask server (full functionality)

## 📁 **Files Ready for GitHub Pages**

### **Required Files:**
```
frontend/
├── index.html                    # Main static frontend
├── static_data/                  # All ETL output files
│   ├── connections.json          # Connection registry
│   ├── data_sources.json         # Frontend-compatible data
│   ├── aggregations/             # Geographic data
│   │   ├── regions/
│   │   ├── states/
│   │   ├── zipcodes/
│   │   └── state_regions/
│   └── statistics/               # Statistical data
│       ├── states/
│       ├── zipcodes/
│       └── metadata files
└── README.md                     # Deployment instructions
```

## 🔧 **Deployment Steps**

### **Option 1: Direct GitHub Pages Deployment**

1. **Create GitHub Repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: RE Market Tool static frontend"
   git branch -M main
   git remote add origin https://github.com/yourusername/re-market-tool.git
   git push -u origin main
   ```

2. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Source: Deploy from a branch
   - Branch: main
   - Folder: / (root)
   - Save

3. **Access Your Site:**
   - URL: `https://yourusername.github.io/re-market-tool/`
   - The `index.html` will be served automatically

### **Option 2: GitHub Actions Deployment**

1. **Create `.github/workflows/deploy.yml`:**
   ```yaml
   name: Deploy to GitHub Pages
   
   on:
     push:
       branches: [ main ]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Setup Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.12'
         
         - name: Install dependencies
           run: |
             pip install -r requirements.txt
         
         - name: Run ETL Pipeline
           run: |
             cd backend/scripts
             python update.py --full
         
         - name: Generate Static Files
           run: |
             cd backend/scripts
             python static_generator.py
         
         - name: Deploy to GitHub Pages
           uses: peaceiris/actions-gh-pages@v3
           with:
             github_token: ${{ secrets.GITHUB_TOKEN }}
             publish_dir: ./frontend
   ```

## 🎯 **Static Mode Features**

### **✅ Available:**
- Browse all data sources (37 connections)
- View market overview and statistics
- Analyze geographic data (regions, states, ZIP codes)
- View statistical analysis (20+ metrics)
- Responsive design for mobile/desktop
- Fast loading (no server required)

### **❌ Not Available:**
- Add new data sources
- Modify existing connections
- Trigger ETL processes
- Real-time data updates

## 🔄 **Updating Static Data**

### **Manual Update:**
```bash
# 1. Run ETL pipeline
cd backend/scripts
python update.py --full

# 2. Generate static files
python static_generator.py

# 3. Commit and push
git add frontend/static_data/
git commit -m "Update static data"
git push
```

### **Automatic Update (GitHub Actions):**
The GitHub Actions workflow will automatically:
1. Run the ETL pipeline
2. Generate static files
3. Deploy to GitHub Pages

## 🌐 **Accessing Both Versions**

### **Static Version (GitHub Pages):**
- URL: `https://yourusername.github.io/re-market-tool/`
- Features: Read-only data browsing and analysis
- Cost: Free
- Performance: Fast (static files)

### **Dynamic Version (Flask Server):**
- URL: `http://localhost:5000` (local) or your server URL
- Features: Full functionality including data management
- Cost: Server hosting required
- Performance: Real-time updates

## 📊 **Data Structure**

The static frontend loads data from these JSON files:

- **`data_sources.json`**: List of all available data sources
- **`connections.json`**: Full connection registry with metadata
- **`aggregations/*.json`**: Geographic aggregation data
- **`statistics/*.json`**: Statistical calculations

## 🎨 **Customization**

### **Styling:**
- Edit `frontend/index.html` CSS section
- Responsive design included
- Dark theme optimized

### **Content:**
- Modify the HTML structure in `index.html`
- Add new sections or features
- Update the JavaScript data loading logic

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **404 Error on GitHub Pages:**
   - Ensure `index.html` is in the root directory
   - Check that GitHub Pages is enabled in repository settings

2. **Data Not Loading:**
   - Verify `static_data/` directory exists
   - Check that JSON files are valid
   - Ensure all files are committed to git

3. **CORS Issues:**
   - GitHub Pages serves files with proper CORS headers
   - No additional configuration needed

## 📈 **Performance**

- **Load Time**: < 2 seconds
- **File Size**: ~50KB (HTML + CSS + JS)
- **Data Size**: ~2MB (all JSON files)
- **Compatibility**: All modern browsers

## 🔗 **Links**

- **Repository**: `https://github.com/yourusername/re-market-tool`
- **Live Site**: `https://yourusername.github.io/re-market-tool/`
- **Documentation**: See `README.md` for full project details
