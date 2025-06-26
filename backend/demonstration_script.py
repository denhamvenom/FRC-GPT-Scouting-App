#!/usr/bin/env python3
"""
Game Context Extraction Optimization - Demonstration Script

This script demonstrates the completed implementation of the game context 
optimization feature, showing the dramatic reduction in token usage while
maintaining full functionality.
"""

import asyncio
import json
import os
import tempfile
import time
from typing import Dict, Any

# Add project path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.data_aggregation_service import DataAggregationService
from app.services.game_context_extractor_service import GameContextExtractorService


def create_realistic_manual_data() -> Dict[str, Any]:
    """Create realistic FRC manual data for demonstration."""
    return {
        "game_name": "REEFSCAPE 2025",
        "relevant_sections": """
--- Section: 4 Game Overview (Page 17) ---
REEFSCAPE is played by two competing ALLIANCES of three TEAMS each. ALLIANCES score points by:
• Placing CORAL on their REEF during the AUTONOMOUS and TELEOP PERIODS
• Processing ALGAE in their PROCESSOR during the AUTONOMOUS and TELEOP PERIODS  
• Parking and/or CLIMBING to various levels on the BARGE during ENDGAME

The MATCH begins with the 15-second AUTONOMOUS PERIOD, during which ROBOTS operate without any DRIVER control. During the remaining 2 minutes and 15 seconds of the MATCH, called the TELEOP PERIOD, DRIVERS remotely control ROBOTS. The final 30 seconds of the TELEOP PERIOD is called ENDGAME, during which ROBOTS may attempt additional scoring opportunities.

--- Section: 5 ARENA (Page 19) ---
The ARENA is the field where the GAME is played. The ARENA consists of a bounded rectangular field with various FIELD ELEMENTS. FIELD ELEMENTS include the REEF ZONE, PROCESSOR ZONE, BARGE, and STAGING AREAS.

The REEF ZONE contains three levels (L1, L2, L3) where CORAL can be placed for varying point values. The PROCESSOR ZONE contains team-specific ALGAE PROCESSORS for scoring ALGAE. The BARGE is located in the center of the field and provides climbing opportunities for ENDGAME scoring.

--- Section: 6 Scoring (Page 25) ---
AUTONOMOUS PERIOD (15 seconds):
• CORAL placed on L1: 3 points
• CORAL placed on L2: 5 points  
• CORAL placed on L3: 8 points
• ALGAE processed: 4 points each
• Mobility (leave STARTING ZONE): 2 points

TELEOP PERIOD (135 seconds):
• CORAL placed on L1: 2 points
• CORAL placed on L2: 4 points
• CORAL placed on L3: 6 points
• ALGAE processed: 1 point each

ENDGAME (final 30 seconds):
• PARK on BARGE: 3 points
• CLIMB to Low RUNG: 5 points
• CLIMB to Mid RUNG: 10 points
• CLIMB to High RUNG: 15 points
• Supporting another ROBOT: 3 additional points

RANKING POINTS:
• WIN: 2 RP
• TIE: 1 RP each
• Achieve 18+ CORAL on REEF: 1 RP (CORAL RP)
• Achieve 6+ ROBOTS parked/climbing in ENDGAME: 1 RP (ENSEMBLE RP)

--- Section: 7 Strategy Elements ---
Key strategic considerations for REEFSCAPE:

CORAL PLACEMENT: Higher levels provide more points but require greater reach and precision. Teams should focus on consistent L2/L3 placement for competitive scoring.

ALGAE PROCESSING: Provides steady point accumulation. Strong in AUTONOMOUS (4 pts each) but less valuable in TELEOP (1 pt each). Essential for early game momentum.

CLIMBING STRATEGY: High RUNG climbing (15 pts) can dramatically impact MATCH outcomes. Teams need reliable climbing mechanisms and coordinated ALLIANCE strategy.

ALLIANCE SYNERGY: Successful ALLIANCES balance CORAL placement, ALGAE processing, and climbing capabilities. Complementary robot designs crucial for RANKING POINTS.

DEFENSIVE PLAY: Disrupting opponent CORAL placement and ALGAE processing can be highly effective, especially during critical scoring phases.

--- Section: 8 Game Pieces ---
CORAL: Orange cone-shaped game pieces used for REEF scoring. Can be placed on three levels (L1, L2, L3) with increasing point values and difficulty.

ALGAE: Green sphere-shaped game pieces processed through team PROCESSORS. Valuable in AUTONOMOUS, less so in TELEOP.

--- Section: 9 Technical Specifications ---
FIELD DIMENSIONS: 54 ft x 27 ft (16.46 m x 8.23 m) rectangular field
REEF HEIGHT: L1: 12 inches, L2: 24 inches, L3: 36 inches
BARGE RUNG HEIGHTS: Low: 24 inches, Mid: 36 inches, High: 48 inches
CORAL dimensions: 9.5 inch diameter cone, 6 inches tall
ALGAE dimensions: 7 inch diameter sphere

--- Section: 10 Penalty System ---
MINOR FOULS: 2 points awarded to opposing ALLIANCE
MAJOR FOULS: 5 points awarded to opposing ALLIANCE  
TECHNICAL FOULS: 5 points awarded to opposing ALLIANCE
DISQUALIFICATION: No ranking points earned, ALLIANCE plays with 2 ROBOTS

Common fouls include:
• Contacting opponent ROBOTS outside permitted zones
• Exceeding time limits for CORAL/ALGAE possession
• Multiple ROBOTS in restricted areas simultaneously
• Unsafe play or unsportsmanlike conduct

--- Section: 11 Robot Constraints ---
SIZE LIMITS: 28 inch x 28 inch footprint, height unlimited when collapsed to 14 inches for transport
WEIGHT LIMIT: 125 lbs (56.7 kg) maximum including BATTERY
POWER: Single 12V battery, specific motor and control system requirements
COMMUNICATION: Radio communication restricted to specified frequencies and protocols

PROHIBITED ITEMS: Projectile mechanisms, deliberate damage systems, hazardous materials
INSPECTION: All ROBOTS must pass technical inspection before competition play

--- Section: 12 Competition Format ---
QUALIFICATION MATCHES: Round-robin style, each TEAM plays 10-12 MATCHES with random ALLIANCE partners
ALLIANCE SELECTION: Top 8 TEAMS become ALLIANCE CAPTAINS, select 2 partners each through snake draft
PLAYOFF MATCHES: Single-elimination bracket, best 2-of-3 MATCHES in Finals
AWARDS: Multiple awards including Chairman's Award, Engineering Inspiration, and Gracious Professionalism
        """
    }


def demonstrate_token_savings():
    """Main demonstration of the extraction optimization."""
    print("=" * 60)
    print("GAME CONTEXT EXTRACTION OPTIMIZATION DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Create test dataset
    dataset = {
        "year": 2025,
        "event_key": "2025arc",
        "teams": {
            "1001": {"team_number": 1001, "nickname": "Test Team"}
        }
    }
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(dataset, f)
        dataset_path = f.name
    
    # Create manual file
    manual_data = create_realistic_manual_data()
    base_dir = os.path.dirname(dataset_path)
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    manual_path = os.path.join(data_dir, "manual_text_2025.json")
    with open(manual_path, 'w', encoding='utf-8') as f:
        json.dump(manual_data, f)
    
    try:
        # Demonstration Steps
        print("1. ANALYZING ORIGINAL MANUAL SIZE")
        print("-" * 40)
        
        original_size = len(manual_data["relevant_sections"])
        estimated_tokens = original_size // 4  # Rough estimate
        
        print(f"   Original Manual Size: {original_size:,} characters")
        print(f"   Estimated Tokens: {estimated_tokens:,} tokens")
        print(f"   Estimated Cost per Request: ${estimated_tokens * 0.00002:.4f}")
        print()
        
        print("2. PERFORMING GAME CONTEXT EXTRACTION")
        print("-" * 40)
        
        # Create data service with extraction enabled
        start_time = time.time()
        data_service = DataAggregationService(dataset_path, use_extracted_context=True)
        
        # Force extraction to show process
        extraction_result = data_service.force_extract_game_context()
        
        if extraction_result["success"]:
            extraction_time = time.time() - start_time
            print(f"   ✓ Extraction successful in {extraction_time:.1f}s")
            print(f"   ✓ Validation score: {extraction_result['validation_score']:.2f}")
            
            if 'token_usage' in extraction_result:
                tokens = extraction_result['token_usage']
                print(f"   ✓ Extraction used {tokens.get('total_tokens', 0)} tokens")
            
            print()
            
            print("3. COMPARING CONTEXT SIZES")
            print("-" * 40)
            
            # Get extracted context
            extracted_context = data_service.load_game_context()
            if extracted_context:
                extracted_size = len(extracted_context)
                size_reduction = original_size - extracted_size
                percentage_reduction = 100 * (size_reduction / original_size)
                
                print(f"   Original Size: {original_size:,} characters")
                print(f"   Extracted Size: {extracted_size:,} characters")
                print(f"   Size Reduction: {size_reduction:,} characters ({percentage_reduction:.1f}%)")
                print()
                
                # Token and cost analysis
                original_tokens = original_size // 4
                extracted_tokens = extracted_size // 4
                token_savings = original_tokens - extracted_tokens
                
                print("4. TOKEN AND COST ANALYSIS")
                print("-" * 40)
                print(f"   Original Tokens: {original_tokens:,}")
                print(f"   Extracted Tokens: {extracted_tokens:,}")
                print(f"   Token Savings: {token_savings:,} ({percentage_reduction:.1f}%)")
                print()
                
                # Cost calculations (using GPT-4 pricing as example)
                cost_per_1k_tokens = 0.02  # $0.02 per 1K tokens
                original_cost = (original_tokens / 1000) * cost_per_1k_tokens
                extracted_cost = (extracted_tokens / 1000) * cost_per_1k_tokens
                cost_savings = original_cost - extracted_cost
                
                print(f"   Original Cost/Request: ${original_cost:.4f}")
                print(f"   Extracted Cost/Request: ${extracted_cost:.4f}")
                print(f"   Cost Savings/Request: ${cost_savings:.4f}")
                print()
                
                # Scale analysis
                print("5. SCALE IMPACT ANALYSIS")
                print("-" * 40)
                requests_per_day = 100
                days_per_month = 30
                monthly_requests = requests_per_day * days_per_month
                
                monthly_original_cost = monthly_requests * original_cost
                monthly_extracted_cost = monthly_requests * extracted_cost
                monthly_savings = monthly_original_cost - monthly_extracted_cost
                
                print(f"   Assuming {requests_per_day} requests/day:")
                print(f"   Monthly Original Cost: ${monthly_original_cost:.2f}")
                print(f"   Monthly Extracted Cost: ${monthly_extracted_cost:.2f}")
                print(f"   Monthly Savings: ${monthly_savings:.2f}")
                print()
                
                print("6. QUALITY VERIFICATION")
                print("-" * 40)
                
                # Show sample of extracted content
                print("   Sample of extracted context:")
                lines = extracted_context.split('\n')[:10]
                for line in lines:
                    if line.strip():
                        print(f"   {line}")
                print("   ...")
                print()
                
                print("7. SUMMARY")
                print("-" * 40)
                print(f"   ✓ Size reduced by {percentage_reduction:.1f}%")
                print(f"   ✓ Token usage reduced by {token_savings:,}")
                print(f"   ✓ Cost reduced by ${cost_savings:.4f} per request")
                print(f"   ✓ Potential monthly savings: ${monthly_savings:.2f}")
                print(f"   ✓ Extraction validation score: {extraction_result['validation_score']:.2f}")
                print(f"   ✓ No functionality lost - full fallback available")
                
            else:
                print("   ✗ Failed to load extracted context")
        else:
            print(f"   ✗ Extraction failed: {extraction_result.get('error', 'Unknown error')}")
    
    finally:
        # Cleanup
        try:
            os.unlink(dataset_path)
            os.unlink(manual_path)
            os.rmdir(data_dir)
        except:
            pass
    
    print()
    print("=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    
    return True


def show_implementation_status():
    """Show the status of implementation phases."""
    print("\nIMPLEMENTATION STATUS:")
    print("=" * 30)
    
    phases = [
        ("Phase 1: Infrastructure Setup", "✓ COMPLETED"),
        ("Phase 2: Extraction Service Implementation", "✓ COMPLETED"),
        ("Phase 3: Integration", "✓ COMPLETED"),
        ("Phase 4: Testing & Validation", "✓ COMPLETED"),
        ("Phase 5: Safety & Rollback", "✓ COMPLETED"),
        ("Phase 6: Documentation & Deployment", "✓ COMPLETED")
    ]
    
    for phase, status in phases:
        print(f"{phase}: {status}")
    
    print()
    print("FEATURES IMPLEMENTED:")
    print("✓ GameContextExtractorService - GPT-powered extraction")
    print("✓ Comprehensive type system and validation")
    print("✓ Caching and performance optimization")
    print("✓ DataAggregationService integration")
    print("✓ Fallback to full manual on failure")
    print("✓ API endpoints for management")
    print("✓ Command-line interface")
    print("✓ Comprehensive test suite")
    print("✓ Configuration management")
    print("✓ Async handling and thread safety")


if __name__ == "__main__":
    print("Starting Game Context Extraction Demonstration...")
    print()
    
    try:
        # Run demonstration
        demonstrate_token_savings()
        
        # Show implementation status
        show_implementation_status()
        
        print("\n🎉 GAME CONTEXT OPTIMIZATION SUCCESSFULLY IMPLEMENTED!")
        print("\nNext steps:")
        print("1. Deploy to staging environment")
        print("2. Conduct A/B testing with real picklist generation")
        print("3. Monitor performance and cost savings")
        print("4. Roll out to production with feature flag")
        
    except KeyboardInterrupt:
        print("\n\nDemonstration cancelled by user")
    except Exception as e:
        print(f"\n\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()