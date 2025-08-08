# 📱 Usage Guide - Automotive Chatbot Platform

## 🚀 Getting Started

### Quick Launch
```bash
# Start all services
npm run dev:all

# Or with Rasa included
npm run dev:all-with-rasa
```

**Access Points After Launch:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000  
- **API Docs**: http://localhost:8000/docs
- **Rasa API**: http://localhost:5005 (if running)

## 🎯 Core Features

### 1. Chat Interface
- **Real-time messaging** with AI assistant
- **Automotive expertise** - cars, COE, pricing, services
- **Singapore-specific** automotive information
- **Multi-language support** (English primary)

### 2. Car Information Queries
```
User: "What's the price of a Toyota Camry?"
Bot: "The Toyota Camry starts from $XXX,XXX in Singapore..."

User: "Tell me about Honda Civic features"
Bot: "The Honda Civic comes with..."
```

### 3. COE (Certificate of Entitlement) Data
```
User: "What's the current COE price?"
Bot: "Current COE prices: Category A: $XXX, Category B: $XXX..."

User: "COE bidding results"
Bot: "Latest COE bidding results..."
```

### 4. Car Loans & Financing
```
User: "Car loan calculator"
Bot: "I can help calculate your car loan..."

User: "What banks offer car loans?"
Bot: "Banks offering car loans in Singapore..."
```

## 🛠️ Developer Usage

### API Endpoints

#### **Chat with Bot**
```bash
POST http://localhost:8000/api/chat
Content-Type: application/json

{
  "message": "Hello, I want to know about cars",
  "user_id": "user123",
  "session_id": "session456"
}
```

#### **Get Car Information**
```bash
GET http://localhost:8000/api/cars?model=camry
GET http://localhost:8000/api/cars/toyota
```

#### **COE Data**
```bash
GET http://localhost:8000/api/coe/current
GET http://localhost:8000/api/coe/history
```

#### **Health Check**
```bash
GET http://localhost:8000/health
```

### Direct Rasa API
```bash
# Send message to Rasa
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "user123",
    "message": "I want to buy a car"
  }'
```

## 📊 Admin Features

### Database Management
```bash
# Setup MongoDB
python mongodb_setup.py

# Check database connection
npm run db:check

# View collections
python -c "
import pymongo
client = pymongo.MongoClient('mongodb://localhost:27017')
db = client.automotive_chatbot
print(db.list_collection_names())
"
```

### Model Training
```bash
# Train Rasa model
npm run rasa:train

# Download spaCy model
npm run spacy:download

# Validate training data
cd backend && rasa data validate
```

### Service Status
```bash
# Check all services
npm run status

# Individual checks
curl http://localhost:3000        # Frontend
curl http://localhost:8000/health # Backend
curl http://localhost:5005/status # Rasa
```

## 🎨 Frontend Usage

### Chat Interface Components
1. **Message Input** - Type your automotive questions
2. **Chat History** - View conversation history  
3. **Quick Actions** - Pre-defined common queries
4. **Settings** - Configure preferences

### Sample Conversations

#### **Car Purchase Inquiry**
```
You: "I want to buy a family car under $100k"
Bot: "For family cars under $100k, I recommend:
     - Toyota Altis: Starting from $X
     - Honda Civic: Starting from $Y  
     - Mazda CX-5: Starting from $Z
     Would you like details on any specific model?"

You: "Tell me more about Honda Civic"
Bot: "Honda Civic 2024 features:
     - Engine: 1.5L VTEC Turbo
     - Fuel efficiency: 6.7L/100km
     - Safety: Honda SENSING
     - Price: $XXX,XXX (excluding COE)
     Would you like to know about financing options?"
```

#### **COE Information**
```
You: "What's happening with COE prices?"
Bot: "Current COE trends:
     📈 Category A: $XX,XXX (+$X,XXX from last round)
     📈 Category B: $XX,XXX (+$X,XXX from last round)
     📊 Next bidding: [Date]
     
     COE prices have been trending upward due to..."
```

## 🔧 Customization

### Adding New Car Models
1. **Update training data** in `backend/data/nlu.yml`
2. **Add car details** to database
3. **Retrain model**: `npm run rasa:train`

### Custom Responses
Edit `backend/data/domain.yml`:
```yaml
responses:
  utter_custom_greeting:
  - text: "Welcome to Singapore's #1 automotive assistant!"
  - text: "Hello! Ready to find your perfect car?"
```

### API Integration
Add new endpoints in `backend/api/routes/`:
```python
@router.get("/api/custom-feature")
async def custom_feature():
    return {"message": "Custom feature response"}
```

## 🚨 Troubleshooting Usage

### Common User Issues

#### **Chat Not Responding**
1. Check if backend is running: `curl http://localhost:8000/health`
2. Verify Rasa is running: `curl http://localhost:5005/status`
3. Check browser console for errors

#### **Outdated Information**
1. Update data sources in `backend/utils/data_fetcher.py`
2. Refresh car database: `python backend/scripts/update_car_data.py`
3. Retrain model: `npm run rasa:train`

#### **Slow Response Times**
1. Check system resources (RAM, CPU)
2. Restart services: `npm run dev:all`
3. Consider using lightweight models

### Developer Issues

#### **API Connection Errors**
```bash
# Check service ports
netstat -an | grep -E "(3000|8000|5005)"

# Restart specific service
cd frontend && npm run dev    # Frontend only
cd backend && uvicorn api.main:app --reload --port 8000  # Backend only
```

#### **Database Connection Issues**
```bash
# Test MongoDB connection
python -c "
import pymongo
try:
    client = pymongo.MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000)
    client.server_info()
    print('✅ MongoDB connected')
except: 
    print('❌ MongoDB not accessible')
"
```

## 📈 Performance Optimization

### Frontend Optimization
- **Enable caching** for static assets
- **Lazy load** components
- **Optimize images** and assets

### Backend Optimization  
- **Use connection pooling** for database
- **Cache frequent queries**
- **Enable GZIP compression**

### Rasa Optimization
- **Use optimized pipeline** in `config.yml`
- **Reduce model size** by removing unused components
- **Enable GPU acceleration** if available

## 🎉 Best Practices

### For End Users
- **Be specific** in your automotive queries
- **Use natural language** - no need for keywords
- **Ask follow-up questions** for detailed information
- **Report issues** for continuous improvement

### For Developers
- **Monitor logs** regularly
- **Update dependencies** periodically  
- **Test after changes** before deployment
- **Document API changes**

## 📱 Mobile Usage

The platform is responsive and works on:
- **Desktop browsers** (Chrome, Firefox, Safari, Edge)
- **Mobile browsers** (iOS Safari, Chrome Mobile)
- **Tablet devices**

Access the same URL: http://localhost:3000

## 🎯 Advanced Usage

### Batch Processing
```python
# Process multiple queries
import requests

queries = [
    "Toyota Camry price",
    "Honda Civic features", 
    "COE Category B price"
]

for query in queries:
    response = requests.post("http://localhost:8000/api/chat", 
                           json={"message": query, "user_id": "batch_user"})
    print(f"Q: {query}")
    print(f"A: {response.json()['response']}\n")
```

### API Integration Example
```javascript
// Frontend integration
const chatAPI = {
  async sendMessage(message, userId) {
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, user_id: userId })
    });
    return response.json();
  }
};

// Usage
const result = await chatAPI.sendMessage("Car loan options", "user123");
console.log(result.response);
```

## 🎉 You're Ready to Use!

Your automotive chatbot platform is fully operational! Whether you're an end user looking for car information or a developer integrating the API, you now have all the tools and knowledge needed to get the most out of the platform. 