# RASA-Style Sequence Diagrams

## Problem 2 Solution: RASA Architecture Sequence Diagrams

### Monthly Installment Calculation - RASA Style

```
User Input: "Calculate loan for $100,000 car, 5 years, 3.5% interest"

(1) newInput() ────────────► InputProvider
                              │
(2) handleInput() ─────────► IntentRecognitionProvider
                              │
(3) extract() ◄──────────── JarvisCore
                              │
(4) create() ─────────────► RecognizedIntent
                              │
(5) rIntent ─────────────► ActionRegistry
                              │
(6) get(rIntent) ─────────► PlatformRegistry
                              │
(7) actions ◄──────────────│
                              │
Loop [action in actions]      │
    (8) get(action) ──────► ActionRunner
                              │
    (9) platform ──────────► PlatformInstance
                              │
    (10) getSession(i, action) ◄─────────│
                              │
    (11) build(action, session) ────────► ActionInstance
                              │
    (12) create ──────────► │
                              │
    (13) aInstance ◄──────│
                              │
    (14) execute(aInstance, session) ──► ActionRunner
                              │
    (15) result ◄──────────│
                              │
    (16) updateSession(session, result) ◄─│
```

### Vehicle Information Retrieval - RASA Style

```
User Input: "Tell me about Toyota Camry"

(1) newInput() ────────────► InputProvider
                              │
(2) handleInput() ─────────► IntentRecognitionProvider
                              │ Intent: ask_vehicle_info
                              │ Entities: brand="Toyota", model="Camry"
(3) extract() ◄──────────── JarvisCore
                              │
(4) create() ─────────────► RecognizedIntent
                              │
(5) rIntent ─────────────► ActionRegistry
                              │ action_get_vehicle_info
(6) get(rIntent) ─────────► PlatformRegistry
                              │
(7) actions ◄──────────────│
                              │
Loop [action in actions]      │
    (8) get(action) ──────► ActionRunner
                              │
    (9) platform ──────────► PlatformInstance
                              │ (load_vehicle_data)
    (10) getSession(i, action) ◄─────────│
                              │ (extract_vehicle_details)
    (11) build(action, session) ────────► ActionInstance
                              │ (find_vehicle_in_data)
    (12) create ──────────► │ (format_response)
                              │
    (13) aInstance ◄──────│
                              │
    (14) execute(aInstance, session) ──► ActionRunner
                              │ Vehicle Info Response
    (15) result ◄──────────│
                              │
    (16) updateSession(session, result) ◄─│
```

### Email Contact Request - RASA Style

```
User Input: "how can i email you"

(1) newInput() ────────────► InputProvider
                              │
(2) handleInput() ─────────► IntentRecognitionProvider
                              │ Intent: ask_email_only
(3) extract() ◄──────────── JarvisCore
                              │
(4) create() ─────────────► RecognizedIntent
                              │
(5) rIntent ─────────────► ActionRegistry
                              │ action_email_only
(6) get(rIntent) ─────────► PlatformRegistry
                              │
(7) actions ◄──────────────│
                              │
Loop [action in actions]      │
    (8) get(action) ──────► ActionRunner
                              │
    (9) platform ──────────► PlatformInstance
                              │
    (10) getSession(i, action) ◄─────────│
                              │
    (11) build(action, session) ────────► ActionInstance
                              │
    (12) create ──────────► │
                              │
    (13) aInstance ◄──────│
                              │
    (14) execute(aInstance, session) ──► ActionRunner
                              │ "📧 Email me now: info@clevercompanion.sg"
    (15) result ◄──────────│
                              │
    (16) updateSession(session, result) ◄─│
```

### COE Price Request - RASA Style

```
User Input: "What are the current COE prices?"

(1) newInput() ────────────► InputProvider
                              │
(2) handleInput() ─────────► IntentRecognitionProvider
                              │ Intent: ask_coe_prices
(3) extract() ◄──────────── JarvisCore
                              │
(4) create() ─────────────► RecognizedIntent
                              │
(5) rIntent ─────────────► ActionRegistry
                              │ action_coe_prices
(6) get(rIntent) ─────────► PlatformRegistry
                              │
(7) actions ◄──────────────│
                              │
Loop [action in actions]      │
    (8) get(action) ──────► ActionRunner
                              │
    (9) platform ──────────► PlatformInstance
                              │ (extract_coe_query_details)
    (10) getSession(i, action) ◄─────────│
                              │ (format_change)
    (11) build(action, session) ────────► ActionInstance
                              │ (historical_data_lookup)
    (12) create ──────────► │
                              │
    (13) aInstance ◄──────│
                              │
    (14) execute(aInstance, session) ──► ActionRunner
                              │ COE Prices Response
    (15) result ◄──────────│
                              │
    (16) updateSession(session, result) ◄─│
```

### Maintenance Tips Request - RASA Style

```
User Input: "how to check tire pressure"

(1) newInput() ────────────► InputProvider
                              │
(2) handleInput() ─────────► IntentRecognitionProvider
                              │ Intent: ask_maintenance
(3) extract() ◄──────────── JarvisCore
                              │
(4) create() ─────────────► RecognizedIntent
                              │
(5) rIntent ─────────────► ActionRegistry
                              │ action_get_maintenance_info
(6) get(rIntent) ─────────► PlatformRegistry
                              │
(7) actions ◄──────────────│
                              │
Loop [action in actions]      │
    (8) get(action) ──────► ActionRunner
                              │
    (9) platform ──────────► PlatformInstance
                              │ (search_maintenance_docs)
    (10) getSession(i, action) ◄─────────│
                              │ (RAG_query_processing)
    (11) build(action, session) ────────► ActionInstance
                              │ (format_maintenance_response)
    (12) create ──────────► │
                              │
    (13) aInstance ◄──────│
                              │
    (14) execute(aInstance, session) ──► ActionRunner
                              │ Tire Pressure Instructions
    (15) result ◄──────────│
                              │
    (16) updateSession(session, result) ◄─│
``` 