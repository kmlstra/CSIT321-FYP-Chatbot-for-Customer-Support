"""
RASA Custom Actions - Main Import File
All actions are now split into separate files for better scalability and maintainability
"""

# Import COE-related actions
from .coe_actions import ActionCOEPrices, ActionExplainCOERenewal, ActionExplainCOECategories, ActionCOECategoryA, ActionCOECategoryB, ActionCOECategoryC, ActionCOECategoryE

# Import Loan-related actions  
from .loan_actions import ActionCalculateLoan, ActionLoanOptions, ActionBudgetCalculator, ActionLoanCalculationResult

# Import Feedback-related actions
from .feedback_actions import ActionFeedbackRequest, ActionProcessFeedback, ActionGetCarReviews, ActionShowCarReviews

# Import Contact-related actions
from .contact_actions import (
    ActionEmailOnly, ActionPhoneOnly, ActionWhatsAppOnly,
    ActionContactUs, ActionStoreLocation, ActionOperatingHours
)

# Import Vehicle-related actions
from .vehicle_actions import (
    ActionGetVehicleInfo, ActionBookTestDrive, ActionRecommendEconomicCars, ActionRecommendFamilyCars, ActionSearchVehicles, ActionPersonaBasedRecommendations
)

# Import Fuel-related actions
from .fuel_actions import ActionFuelPrices, ActionCheapestFuel

# Import Maintenance-related actions
from .maintenance_actions import (
    ActionMaintenanceGuide, ActionTireMaintenance, ActionEngineMaintenance, 
    ActionBrakeMaintenance, ActionElectricalMaintenance, ActionFluidMaintenance, ActionFilterMaintenance, ActionGetMaintenanceInfo
)

# Import Test Drive Booking actions
from .testdrive_actions import ActionTestDriveBooking, ActionProcessTestDriveBooking, ActionConfirmTestDriveBooking

# Import Default actions
from .default_actions import ActionDefaultFallback

# Export all actions for RASA to discover
__all__ = [
    # COE Actions
    'ActionCOEPrices',
    'ActionExplainCOERenewal',
    'ActionExplainCOECategories',
    'ActionCOECategoryA',
    'ActionCOECategoryB',
    'ActionCOECategoryC',
    'ActionCOECategoryE',
    
    # Loan Actions
    'ActionCalculateLoan',
    'ActionLoanOptions',
    'ActionBudgetCalculator',
    'ActionLoanCalculationResult',
    
    # Feedback Actions
    'ActionFeedbackRequest',
    'ActionProcessFeedback',
    'ActionGetCarReviews',
    'ActionShowCarReviews',
    
    # Contact Actions
    'ActionEmailOnly',
    'ActionPhoneOnly', 
    'ActionWhatsAppOnly',
    'ActionContactUs',
    'ActionStoreLocation',
    'ActionOperatingHours',
    
    # Vehicle Actions
    'ActionGetVehicleInfo',
    'ActionBookTestDrive',
    'ActionRecommendEconomicCars',
    'ActionRecommendFamilyCars',
    'ActionSearchVehicles',
    'ActionPersonaBasedRecommendations',
    
    # Fuel Actions
    'ActionFuelPrices',
    'ActionCheapestFuel',
    
    # Maintenance Actions
    'ActionMaintenanceGuide',
    'ActionGetMaintenanceInfo',
    'ActionTireMaintenance',
    'ActionEngineMaintenance',
    'ActionBrakeMaintenance',
    'ActionElectricalMaintenance',
    'ActionFluidMaintenance',
    'ActionFilterMaintenance',
    
    # Test Drive Booking Actions
    'ActionTestDriveBooking',
    'ActionProcessTestDriveBooking',
    'ActionConfirmTestDriveBooking',
    
    # Default Actions
    'ActionDefaultFallback'
]