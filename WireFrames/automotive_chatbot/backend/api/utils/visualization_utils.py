"""
🎨 Visualization Utils for Automotive Chatbot
Lightweight chart generation for COE prices and market analysis
Compatible with existing statistical system
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import base64
import io
import os
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

# Set matplotlib to use non-interactive backend for server environments
plt.switch_backend('Agg')

# Configure matplotlib for clean charts optimized for chat interface
plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
plt.rcParams['figure.figsize'] = (10, 6)  # Reduced size for chat interface
plt.rcParams['font.size'] = 9
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9

# Singapore automotive colors
COLORS = {
    'A': '#FF6B6B',    # Red for Category A
    'B': '#4ECDC4',    # Teal for Category B  
    'C': '#45B7D1',    # Blue for Category C
    'D': '#96CEB4',    # Green for Category D
    'E': '#FFEAA7',    # Yellow for Category E
    'trend': '#2C3E50',
    'prediction': '#E74C3C',
    'background': '#F8F9FA'
}

def create_coe_price_chart(current_prices: Dict, historical_data: List[Dict], 
                          chart_type: str = 'trend') -> Optional[str]:
    """
    Create COE price visualization charts
    
    Args:
        current_prices: Current COE prices by category
        historical_data: Historical price data
        chart_type: 'trend', 'comparison', 'volatility', or 'prediction'
    
    Returns:
        Base64 encoded image string
    """
    try:
        fig, ax = plt.subplots(figsize=(8, 5))  # Compact size for chat interface
        
        if chart_type == 'trend':
            _create_trend_chart(ax, current_prices, historical_data)
        elif chart_type == 'comparison':
            _create_comparison_chart(ax, current_prices)
        elif chart_type == 'volatility':
            _create_volatility_chart(ax, historical_data)
        elif chart_type == 'prediction':
            _create_prediction_chart(ax, current_prices, historical_data)
        
        # Convert to base64 for web embedding with optimized settings for chat
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=120, bbox_inches='tight',
                   facecolor='white', edgecolor='none', pad_inches=0.1)
        img_buffer.seek(0)
        
        img_base64 = base64.b64encode(img_buffer.read()).decode()
        plt.close(fig)
        
        return f"data:image/png;base64,{img_base64}"
        
    except Exception as e:
        print(f"Error creating chart: {e}")
        return None

def _create_trend_chart(ax, current_prices: Dict, historical_data: List[Dict]):
    """Create historical trend chart"""
    if not historical_data:
        ax.text(0.5, 0.5, 'No historical data available', 
                ha='center', va='center', transform=ax.transAxes, fontsize=16)
        return
    
    # Prepare data
    dates = [record['date'] for record in historical_data]
    categories = ['A', 'B', 'C', 'D', 'E']
    
    # Plot each category
    for category in categories:
        if category in current_prices:
            prices = []
            valid_dates = []
            
            for i, record in enumerate(historical_data):
                if category in record and record[category] > 0:
                    prices.append(record[category])
                    valid_dates.append(dates[i])
            
            if prices:
                ax.plot(valid_dates, prices, marker='o', linewidth=2.5, 
                       markersize=4, label=f'Category {category}', 
                       color=COLORS[category], alpha=0.8)
    
    # Formatting optimized for chat interface
    ax.set_title('COE Price Trends - Historical Analysis', fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel('Date', fontsize=10)
    ax.set_ylabel('Price (SGD)', fontsize=10)
    ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=False, fontsize=8)
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Format y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Add current price annotations
    for category, price in current_prices.items():
        if category in categories:
            ax.annotate(f'${price:,}', 
                       xy=(dates[-1] if dates else datetime.now(), price),
                       xytext=(10, 10), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor=COLORS[category], alpha=0.7),
                       fontsize=8, fontweight='bold')

def _create_comparison_chart(ax, current_prices: Dict):
    """Create current price comparison bar chart"""
    categories = list(current_prices.keys())
    prices = list(current_prices.values())
    colors = [COLORS.get(cat, '#95A5A6') for cat in categories]
    
    bars = ax.bar(categories, prices, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
    
    # Add value labels on bars
    for bar, price in zip(bars, prices):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(prices)*0.01,
                f'${price:,}', ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    ax.set_title('Current COE Prices by Category', fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel('COE Category', fontsize=10)
    ax.set_ylabel('Price (SGD)', fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax.grid(True, alpha=0.3, axis='y')

def _create_volatility_chart(ax, historical_data: List[Dict]):
    """Create price volatility analysis chart"""
    if len(historical_data) < 6:
        ax.text(0.5, 0.5, 'Insufficient data for volatility analysis', 
                ha='center', va='center', transform=ax.transAxes, fontsize=16)
        return
    
    categories = ['A', 'B', 'C', 'D', 'E']
    volatilities = {}
    
    # Calculate volatility for each category
    for category in categories:
        prices = [record[category] for record in historical_data if category in record and record[category] > 0]
        if len(prices) >= 3:
            changes = []
            for i in range(1, len(prices)):
                change = (prices[i] - prices[i-1]) / prices[i-1]
                changes.append(change)
            
            if changes:
                mean_change = sum(changes) / len(changes)
                variance = sum((change - mean_change) ** 2 for change in changes) / len(changes)
                volatilities[category] = (variance ** 0.5) * 100  # Convert to percentage
    
    if volatilities:
        cats = list(volatilities.keys())
        vols = list(volatilities.values())
        colors = [COLORS.get(cat, '#95A5A6') for cat in cats]
        
        bars = ax.bar(cats, vols, color=colors, alpha=0.8, edgecolor='white', linewidth=2)
        
        # Add value labels
        for bar, vol in zip(bars, vols):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(vols)*0.01,
                    f'{vol:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=9)
    
    ax.set_title('COE Price Volatility Analysis', fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel('COE Category', fontsize=10)
    ax.set_ylabel('Volatility (%)', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

def _create_prediction_chart(ax, current_prices: Dict, historical_data: List[Dict]):
    """Create prediction chart with confidence intervals"""
    if not historical_data:
        ax.text(0.5, 0.5, 'No data available for predictions', 
                ha='center', va='center', transform=ax.transAxes, fontsize=16)
        return
    
    # Use existing prediction logic (simplified version)
    categories = ['A', 'B', 'C', 'D', 'E']
    predictions = {}
    
    for category in categories:
        if category in current_prices:
            prices = [record[category] for record in historical_data if category in record and record[category] > 0]
            if len(prices) >= 3:
                # Simple trend calculation
                recent_prices = prices[-6:] if len(prices) >= 6 else prices
                if len(recent_prices) >= 2:
                    trend = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
                    next_month = max(0, int(current_prices[category] + trend))
                    three_month = max(0, int(current_prices[category] + trend * 3))
                    predictions[category] = {
                        'current': current_prices[category],
                        'next_month': next_month,
                        'three_month': three_month
                    }
    
    if predictions:
        x_pos = range(len(predictions))
        categories = list(predictions.keys())
        current = [predictions[cat]['current'] for cat in categories]
        next_month = [predictions[cat]['next_month'] for cat in categories]
        three_month = [predictions[cat]['three_month'] for cat in categories]
        
        width = 0.25
        ax.bar([x - width for x in x_pos], current, width, label='Current', 
               color='#34495E', alpha=0.8)
        ax.bar(x_pos, next_month, width, label='Next Month (Predicted)', 
               color='#3498DB', alpha=0.8)
        ax.bar([x + width for x in x_pos], three_month, width, label='3 Months (Predicted)', 
               color='#E74C3C', alpha=0.8)
        
        ax.set_title('COE Price Predictions', fontsize=12, fontweight='bold', pad=15)
        ax.set_xlabel('COE Category', fontsize=10)
        ax.set_ylabel('Price (SGD)', fontsize=10)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories)
        ax.legend()
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.grid(True, alpha=0.3, axis='y')

def create_quick_chart_html(chart_base64: str, title: str = "COE Price Chart") -> str:
    """
    Create HTML embed code for charts optimized for chat interface
    
    Args:
        chart_base64: Base64 encoded image
        title: Chart title
    
    Returns:
        HTML string for embedding
    """
    if not chart_base64:
        return f"📊 Chart could not be generated: {title}"
    
    # Use hyphens instead of underscores to avoid italic formatting issues
    chart_id = f"chart-{hash(chart_base64) % 100000}"
    # Use HTML formatting instead of markdown to avoid text formatting interference
    html = f"""
📊 <strong>{title}</strong>

<div class="chart-container">
    <img id="{chart_id}" src="{chart_base64}" alt="{title}" onclick="enlargeChart('{chart_id}', '{title}')" style="cursor: pointer;" title="Click to enlarge">
</div>

<em>Generated by CleverCompanion Analytics</em>


    """.strip()
    return html

def save_chart_to_file(chart_base64: str, filename: str, directory: str = "charts") -> bool:
    """
    Save chart to file system
    
    Args:
        chart_base64: Base64 encoded image
        filename: Filename without extension
        directory: Directory to save in
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Decode base64 and save
        if chart_base64.startswith('data:image/png;base64,'):
            chart_base64 = chart_base64.split(',')[1]
        
        img_data = base64.b64decode(chart_base64)
        filepath = os.path.join(directory, f"{filename}.png")
        
        with open(filepath, 'wb') as f:
            f.write(img_data)
        
        return True
        
    except Exception as e:
        print(f"Error saving chart: {e}")
        return False

# Helper function for integrating with existing actions
def get_chart_for_coe_response(prices: Dict, historical_data: Optional[List[Dict[str, Any]]] = None, 
                              chart_type: str = 'trend') -> Optional[str]:
    """
    Helper function to generate charts for COE responses
    
    Args:
        prices: Current COE prices
        historical_data: Historical data
        chart_type: Type of chart to generate
    
    Returns:
        HTML string with embedded chart or None
    """
    try:
        if historical_data is None:
            historical_data = []
        chart_base64 = create_coe_price_chart(prices, historical_data, chart_type)
        if chart_base64:
            titles = {
                'trend': 'COE Price Trends',
                'comparison': 'Current COE Price Comparison',
                'volatility': 'COE Price Volatility Analysis',
                'prediction': 'COE Price Predictions'
            }
            title = titles.get(chart_type, 'COE Price Chart')
            return create_quick_chart_html(chart_base64, title)
        return None
    except Exception as e:
        print(f"Error generating chart for response: {e}")
        return None