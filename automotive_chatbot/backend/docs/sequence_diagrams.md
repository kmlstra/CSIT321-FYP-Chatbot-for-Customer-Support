# Backend Architecture Documentation

## Sequence Diagrams and Class Diagrams

### Problem 6 Solution: Complete Backend Architecture Documentation

## 1. User Story: Calculate Monthly Installment

**User Story:** As a user, I want to calculate my monthly installment for a car loan.

### Sequence Diagram: Monthly Installment Calculation

```mermaid
sequenceDiagram
    participant User as User (Frontend)
    participant Widget as Chat Widget
    participant RASA as RASA Core
    participant Actions as Actions Server
    participant Backend as FastAPI Backend
    participant DB as Database

    User->>Widget: "Calculate loan for $100,000 car, 5 years, 3.5% interest"
    Widget->>RASA: POST /webhooks/rest/webhook
    Note over Widget,RASA: {"sender": "user_123", "message": "Calculate loan..."}
    
    RASA->>RASA: NLU Processing
    Note over RASA: Intent: calculate_loan<br/>Entities: car_price, tenure, interest_rate
    
    RASA->>Actions: action_calculate_loan
    Note over Actions: Extract loan parameters<br/>Validate required fields
    
    alt Missing Parameters
        Actions->>Actions: Validate input parameters
        Actions-->>RASA: Error response: "Missing down payment amount"
        RASA-->>Widget: Combined error response
        Widget-->>User: "Please provide down payment amount"
    else All Parameters Present
        Actions->>Actions: Calculate monthly payment
        Note over Actions: Formula: P * [r(1+r)^n] / [(1+r)^n - 1]
        
        Actions->>Backend: GET /api/loan/rates (optional)
        Backend->>DB: Query current interest rates
        DB-->>Backend: Rate data
        Backend-->>Actions: Current rates
        
        Actions->>Actions: Generate loan breakdown
        Note over Actions: Monthly payment<br/>Total interest<br/>Total amount
        
        Actions-->>RASA: Formatted loan results
        RASA-->>Widget: Combined response with calculations
        Widget-->>User: Display loan calculator results
    end
```

## 2. User Story: Get Vehicle Information

**User Story:** As a user, I want to get information about a specific vehicle model.

### Sequence Diagram: Vehicle Information Retrieval with RAG

```mermaid
sequenceDiagram
    participant User as User (Frontend)
    participant Widget as Chat Widget
    participant RASA as RASA Core
    participant Actions as Actions Server
    participant Excel as Excel Data Source
    participant Backend as FastAPI Backend

    User->>Widget: "Tell me about Toyota Camry"
    Widget->>RASA: POST /webhooks/rest/webhook
    
    RASA->>RASA: NLU Processing
    Note over RASA: Intent: ask_vehicle_info<br/>Entities: brand="Toyota", model="Camry"
    
    RASA->>Actions: action_get_vehicle_info
    
    Actions->>Actions: load_vehicle_data()
    Note over Actions: Load from singapore_vehicle_data.xlsx
    
    Actions->>Excel: Read Excel file
    Excel-->>Actions: Vehicle dataset (pandas DataFrame)
    
    Actions->>Actions: extract_vehicle_details(user_text)
    Note over Actions: Extract: brand="toyota", model="camry"
    
    Actions->>Actions: find_vehicle_in_data(df, brand, model)
    Note over Actions: Search DataFrame for matching vehicle
    
    alt Vehicle Found in Data
        Actions->>Actions: Format vehicle information
        Note over Actions: Price, specs, features from Excel data
        Actions-->>RASA: Detailed vehicle information
    else Vehicle Not Found
        Actions->>Actions: get_brand_models(df, brand)
        Note over Actions: List available models for brand
        Actions-->>RASA: Available models response
    end
    
    RASA-->>Widget: Vehicle information response
    Widget-->>User: Display vehicle details with specifications
```

## 3. User Story: Get Contact Information

**User Story:** As a user, I want to get contact information (email only).

### Sequence Diagram: Contact Information

```mermaid
sequenceDiagram
    participant User as User (Frontend)
    participant Widget as Chat Widget
    participant RASA as RASA Core
    participant Actions as Actions Server

    User->>Widget: "how can i email you"
    Widget->>RASA: POST /webhooks/rest/webhook
    
    RASA->>RASA: NLU Processing
    Note over RASA: Intent: ask_email_only
    
    RASA->>Actions: action_email_only
    
    Actions->>Actions: Generate email response
    Note over Actions: "📧 Email: info@clevercompanion.sg"
    
    Actions-->>RASA: Email-only response
    RASA-->>Widget: Email contact information
    Widget-->>User: Display email contact
```

## 4. Class Diagram: Backend Architecture

### FastAPI Backend Structure (Post-BCE Removal)

```mermaid
classDiagram
    class FastAPIMain {
        +app: FastAPI
        +start_server()
        +configure_routes()
        +setup_middleware()
    }
    
    class VehicleService {
        +get_vehicle_info(brand: str, model: str): dict
        +search_vehicles(criteria: dict): list
        +load_excel_data(): DataFrame
        +filter_by_brand(brand: str): list
    }
    
    class COEService {
        +get_current_prices(): dict
        +get_historical_data(month: int, year: int): dict
        +predict_future_prices(): dict
        +format_price_changes(): str
    }
    
    class LoanService {
        +calculate_monthly_payment(principal: float, rate: float, tenure: int): dict
        +validate_loan_parameters(params: dict): bool
        +get_bank_rates(): list
        +generate_amortization_schedule(): list
    }
    
    class ContactService {
        +get_all_contact_info(): dict
        +get_email_only(): str
        +get_phone_only(): str
        +get_whatsapp_only(): str
        +get_operating_hours(): dict
    }
    
    class MaintenanceService {
        +get_maintenance_tips(): dict
        +get_service_schedule(): list
        +search_maintenance_docs(query: str): dict
        +get_maintenance_costs(): dict
    }
    
    FastAPIMain --> VehicleService
    FastAPIMain --> COEService
    FastAPIMain --> LoanService
    FastAPIMain --> ContactService
    FastAPIMain --> MaintenanceService
```

## 5. RASA Actions Class Structure

```mermaid
classDiagram
    class ActionBase {
        <<abstract>>
        +name(): str
        +run(dispatcher, tracker, domain): list
        +extract_entities(tracker): dict
    }
    
    class ActionCOEPrices {
        +name(): str = "action_coe_prices"
        +run(): list
        +extract_coe_query_details(text: str): dict
        +format_change(change: int): str
    }
    
    class ActionCalculateLoan {
        +name(): str = "action_calculate_loan"
        +run(): list
        +extract_loan_details(text: str): dict
        +calculate_loan_payment(): dict
        +validate_parameters(): bool
    }
    
    class ActionGetVehicleInfo {
        +name(): str = "action_get_vehicle_info"
        +run(): list
        +load_vehicle_data(): DataFrame
        +extract_vehicle_details(text: str): tuple
        +find_vehicle_in_data(): dict
        +get_brand_models(): str
    }
    
    class ActionOperatingHours {
        +name(): str = "action_operating_hours"
        +run(): list
        +check_specific_day(text: str): dict
        +check_holiday_query(text: str): bool
        +get_full_schedule(): str
    }
    
    class ActionContactInfo {
        +name(): str = "action_contact_info"
        +run(): list
    }
    
    class ActionEmailOnly {
        +name(): str = "action_email_only"
        +run(): list
    }
    
    class ActionPhoneOnly {
        +name(): str = "action_phone_only"
        +run(): list
    }
    
    class ActionWhatsAppOnly {
        +name(): str = "action_whatsapp_only"
        +run(): list
    }
    
    class ActionRecommendEconomicCars {
        +name(): str = "action_recommend_economic_cars"
        +run(): list
        +get_economic_models(): list
        +format_recommendations(): str
    }
    
    ActionBase <|-- ActionCOEPrices
    ActionBase <|-- ActionCalculateLoan
    ActionBase <|-- ActionGetVehicleInfo
    ActionBase <|-- ActionOperatingHours
    ActionBase <|-- ActionContactInfo
    ActionBase <|-- ActionEmailOnly
    ActionBase <|-- ActionPhoneOnly
    ActionBase <|-- ActionWhatsAppOnly
    ActionBase <|-- ActionRecommendEconomicCars
```

## 6. Data Flow Architecture

### Overall System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Chat Widget] --> B[React Dashboard]
        B --> A
    end
    
    subgraph "API Gateway"
        C[RASA Core] --> D[Actions Server]
        D --> C
        C --> E[FastAPI Backend]
        E --> C
    end
    
    subgraph "Business Logic Layer"
        F[Vehicle Service] --> G[COE Service]
        G --> H[Loan Service]
        H --> I[Contact Service]
        I --> J[Maintenance Service]
    end
    
    subgraph "Data Layer"
        K[Excel Files] --> L[Vehicle Data]
        L --> M[COE Historical Data]
        M --> N[Configuration Data]
    end
    
    A --> C
    B --> C
    D --> F
    F --> K
    G --> K
    H --> K
    I --> K
    J --> K
```

## 7. Request/Response Flow

### Complete Request Processing Flow

```mermaid
sequenceDiagram
    participant U as User
    participant W as Widget
    participant R as RASA
    participant A as Actions
    participant S as Services
    participant D as Data

    U->>W: User Input
    W->>R: HTTP POST /webhooks/rest/webhook
    R->>R: NLU Processing (Intent + Entities)
    R->>R: Policy Prediction
    R->>A: Execute Custom Action
    A->>S: Business Logic Call
    S->>D: Data Retrieval
    D-->>S: Raw Data
    S-->>A: Processed Data
    A->>A: Format Response
    A-->>R: Action Response
    R->>R: Generate Final Response
    R-->>W: JSON Response Array
    W->>W: Combine Multiple Responses
    W-->>U: Formatted Message
```

## 8. Error Handling Flow

```mermaid
sequenceDiagram
    participant U as User
    participant W as Widget
    participant R as RASA
    participant A as Actions

    U->>W: Invalid Request
    W->>R: POST Request
    R->>A: Execute Action
    
    alt Action Fails
        A->>A: Log Error
        A-->>R: Error Response
        R-->>W: Fallback Response
        W-->>U: User-friendly Error Message
    else Data Not Found
        A->>A: Handle Missing Data
        A-->>R: "Data not available" Response
        R-->>W: Informative Response
        W-->>U: Helpful Alternative Options
    else Network Timeout
        W->>W: Detect Timeout
        W-->>U: Connection Error Message
    end
```

This documentation covers the complete backend architecture with proper FastAPI structure (removing BCE), comprehensive sequence diagrams for user stories, class diagrams for all major components, and detailed data flow documentation. 