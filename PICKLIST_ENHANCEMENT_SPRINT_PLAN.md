# PICKLIST ENHANCEMENT SPRINT PLAN
**Project**: Enhanced Picklist Generation with Unified Field Selection Labels  
**Version**: 1.0  
**Created**: July 6, 2025  

## INSTRUCTIONS FOR CONTEXT WINDOWS

### CRITICAL: How to Use This Document
**EVERY context window MUST follow these steps:**

1. **READ FIRST**: Always read this entire document before starting any work
2. **USE FOR REFERENCE**: Check previous sprint completion notes for context and dependencies
3. **USE FOR COORDINATION**: Follow the exact copy-paste prompt for your assigned sprint
4. **UPDATE REQUIRED**: After completing work, you MUST update this document with:
   - Specific changes made and file locations
   - Code snippets of key modifications
   - Challenges encountered and solutions
   - Important context for the next sprint
   - Validation results

### Document Update Process
```markdown
### Sprint X Completion Notes
**Changes Made**:
- Updated file_name.py: specific_function_name() to do X
- Added new method new_method_name() in file_name.py lines X-Y
- Modified existing_method() to handle enhanced_data_structure

**Code Locations**:
- /backend/app/services/data_aggregation_service.py:53-78 (updated _load_label_mappings)
- /backend/app/services/picklist_gpt_service.py:43-65 (enhanced _load_scouting_labels)

**Challenges Encountered**:
- Issue with X: solved by Y
- Performance concern Z: addressed with optimization A

**Important Context for Next Sprint**:
- New function available: get_enhanced_labels() returns merged data
- Enhanced data structure confirmed working
- Text field support fully implemented

**Validation Notes**:
- Tested with unified_event_2025lake.json: SUCCESS
- Backward compatibility verified: SUCCESS
- Enhanced label loading confirmed: SUCCESS
```

### Sprint Handoff Requirements
**BEFORE starting your sprint**: Verify all previous sprints are marked complete
**AFTER finishing your sprint**: Mark your sprint complete and update "Last Updated" date
**IF encountering blockers**: Document clearly for next context window to address

---

## PROJECT OVERVIEW

### Goal
Update the picklist functionality to fully utilize the new unified field selection data structure with enhanced labels, descriptions, and text field support for strategy analysis and team ranking.

### Key Requirements
1. **Strategy Description Enhancement**: GPT receives complete label descriptions and text field awareness
2. **Picklist Generation Enhancement**: Team data includes enhanced labels, descriptions, and actual text content
3. **Data Integration**: Prioritize field_selections label_mapping over game_labels for completeness

### Architecture Context
- **Unified Data**: `/backend/app/data/unified_event_2025lake.json` contains team scouting data
- **Field Selections**: `/backend/app/data/field_selections_2025lake.json` contains enhanced label mappings
- **Game Labels**: `/backend/app/data/game_labels_2025.json` contains base label definitions
- **Priority Order**: field_selections.label_mapping → game_labels → fallback

---

## SPRINT 1: Data Loading & Label Management Enhancement
**Estimated Tokens**: ~15,000  
**Focus**: Update core data loading services to use unified structure

### Sprint 1 Objectives
1. Update DataAggregationService to load enhanced field selections
2. Enhance PicklistGPTService label loading with unified data
3. Implement proper label mapping hierarchy
4. Add text field support throughout data pipeline

### Files to Modify
- `/backend/app/services/data_aggregation_service.py`
- `/backend/app/services/picklist_gpt_service.py`

### Key Changes Required
1. **DataAggregationService._load_label_mappings()**: Load from unified field_selections structure first
2. **PicklistGPTService._load_scouting_labels()**: Merge field_selections and game_labels data
3. **Text field integration**: Support strategy_field, scout_comments data types
4. **Enhanced context**: Include usage_context, typical_range in label metadata

### Copy-Paste Prompt for Sprint 1
```
CRITICAL INSTRUCTIONS: Before starting, you MUST read the entire PICKLIST_ENHANCEMENT_SPRINT_PLAN.md document first. Follow ALL instructions in the "INSTRUCTIONS FOR CONTEXT WINDOWS" section.

I need to implement Sprint 1 of the Picklist Enhancement project. 

MANDATORY FIRST STEP: Read /PICKLIST_ENHANCEMENT_SPRINT_PLAN.md completely and verify no previous sprints are incomplete.

CONTEXT: We're updating the picklist functionality to use the new unified field selection data structure. The system currently uses only game_labels_2025.json but needs to prioritize enhanced label_mapping data from field_selections files.

SPRINT 1 OBJECTIVES:
1. Update DataAggregationService to load enhanced field selections with priority: field_selections.label_mapping → game_labels → fallback
2. Enhance PicklistGPTService label loading to merge unified data sources
3. Add text field support (strategy_field, scout_comments) throughout data pipeline
4. Include usage_context, typical_range in label metadata for GPT

KEY FILES TO READ FIRST:
- /PICKLIST_ENHANCEMENT_SPRINT_PLAN.md (CRITICAL: Read instructions section)
- /backend/app/data/field_selections_2025lake.json (see label_mapping structure)
- /backend/app/data/game_labels_2025.json (base label definitions)
- /backend/app/services/data_aggregation_service.py (current implementation)
- /backend/app/services/picklist_gpt_service.py (current label loading)

IMPLEMENTATION PRIORITY:
1. Update DataAggregationService._load_label_mappings() to read unified structure
2. Update PicklistGPTService._load_scouting_labels() to merge data sources
3. Enhance _create_labels_context() with richer metadata
4. Add text field support in _enhance_metrics_with_labels()

MANDATORY COMPLETION REQUIREMENTS (per sprint plan document):
1. Update Sprint 1 Completion Notes section in PICKLIST_ENHANCEMENT_SPRINT_PLAN.md using Edit tool
2. Follow exact template in "Document Update Process" section
3. Include specific changes, code locations, challenges, context for Sprint 2
4. Update "Last Updated" field at bottom of document
5. Verify all Sprint 1 Success Criteria are met before marking complete

FAILURE TO FOLLOW THESE INSTRUCTIONS WILL BREAK PROJECT COORDINATION.

START IMPLEMENTATION.
```

### Sprint 1 Success Criteria
- [x] DataAggregationService loads from unified field_selections structure
- [x] PicklistGPTService merges field_selections and game_labels data
- [x] Text fields (strategy_field, scout_comments) are supported
- [x] Enhanced label context includes usage_context and typical_range
- [x] Backward compatibility maintained

### Sprint 1 Completion Notes
**Changes Made**:
- Updated DataAggregationService._load_label_mappings() in data_aggregation_service.py:53-160 to implement unified field selection priority hierarchy
- Enhanced PicklistGPTService._load_scouting_labels() in picklist_gpt_service.py:43-123 to merge field_selections and game_labels data sources
- Upgraded _create_labels_context() in picklist_gpt_service.py:429-509 with richer metadata including usage_context, typical_range, and data_type
- Modified _apply_label_mappings() in data_aggregation_service.py:839-909 to support text field separation and enhanced metadata
- Updated _aggregate_scouting_metrics() in data_aggregation_service.py:801-860 to handle text data collection and consolidation
- Enhanced prepare_team_data_for_gpt() in picklist_gpt_service.py:125-182 to properly format text fields for GPT analysis

**Code Locations**:
- /backend/app/services/data_aggregation_service.py:53-160 (enhanced _load_label_mappings with priority hierarchy)
- /backend/app/services/data_aggregation_service.py:839-909 (enhanced _apply_label_mappings with text field support)
- /backend/app/services/data_aggregation_service.py:801-860 (updated _aggregate_scouting_metrics for text data)
- /backend/app/services/picklist_gpt_service.py:43-123 (enhanced _load_scouting_labels with unified data sources)
- /backend/app/services/picklist_gpt_service.py:429-509 (enriched _create_labels_context with metadata)
- /backend/app/services/picklist_gpt_service.py:125-182 (updated prepare_team_data_for_gpt for text fields)

**Challenges Encountered**:
- Needed to maintain backward compatibility while implementing enhanced data structures
- Required careful handling of text vs numeric data types throughout pipeline
- Had to balance token efficiency with richer context information for GPT

**Important Context for Sprint 2**:
- Enhanced label loading now works with priority: field_selections.label_mapping → game_labels → fallback
- Text field support fully implemented with strategy_field and scout_comments data types
- New function available: enhanced _load_label_mappings() returns full metadata objects instead of just label strings
- GPT context now includes usage_context, typical_range, and data_type for all metrics
- Team data preparation separates text_data from numeric metrics for proper GPT formatting

**Validation Notes**:
- Tested with field_selections_2025lake.json structure: SUCCESS
- Backward compatibility with game_labels_2025.json maintained: SUCCESS
- Enhanced label loading with metadata confirmed working: SUCCESS
- Text field integration (strategy_field, scout_comments) verified: SUCCESS

---

## SPRINT 2: Strategy Analysis Enhancement
**Estimated Tokens**: ~12,000  
**Focus**: Update strategy description parsing with enhanced labels

### Sprint 2 Objectives
1. Update PicklistAnalysisService to use unified field selections
2. Enhance strategy parsing with complete label descriptions
3. Add category groupings and data type awareness to GPT prompts
4. Improve metric_info preparation with enhanced metadata

### Files to Modify
- `/backend/app/services/picklist_analysis_service.py`

### Key Changes Required
1. **_load_field_selections()**: Use unified field_selections structure
2. **parse_strategy_prompt()**: Include enhanced label descriptions in GPT context
3. **Metric preparation**: Add usage_context, typical_range, data_type to metric_info
4. **GPT prompt enhancement**: Include category groupings and text field awareness

### Copy-Paste Prompt for Sprint 2
```
CRITICAL INSTRUCTIONS: Before starting, you MUST read the entire PICKLIST_ENHANCEMENT_SPRINT_PLAN.md document first. Follow ALL instructions in the "INSTRUCTIONS FOR CONTEXT WINDOWS" section.

I need to implement Sprint 2 of the Picklist Enhancement project.

MANDATORY FIRST STEP: Read /PICKLIST_ENHANCEMENT_SPRINT_PLAN.md completely and verify Sprint 1 is marked as complete with proper completion notes.

CONTEXT: Sprint 1 updated core data loading to use unified field selections. Now we need to enhance strategy description parsing to use the complete enhanced label data.

SPRINT 2 OBJECTIVES:
1. Update PicklistAnalysisService to load from unified field_selections structure
2. Enhance parse_strategy_prompt() to include complete label descriptions in GPT context
3. Add category groupings (autonomous, teleop, endgame, strategic) to GPT prompts
4. Include data_type awareness so GPT knows about text vs numeric fields

KEY FILES TO READ FIRST:
- /PICKLIST_ENHANCEMENT_SPRINT_PLAN.md (CRITICAL: Read instructions section AND Sprint 1 completion notes)
- /backend/app/services/picklist_analysis_service.py (current implementation)
- /backend/app/data/field_selections_2025lake.json (enhanced label_mapping structure)

IMPLEMENTATION PRIORITY:
1. Update _load_field_selections() method for unified structure
2. Enhance parse_strategy_prompt() GPT context with label descriptions
3. Add metric_info preparation with usage_context and typical_range
4. Update GPT prompt to include category groupings and text field awareness

DEPENDENCIES FROM SPRINT 1 (verify in sprint plan document):
- Enhanced label loading should be working
- Text field support should be implemented
- Unified data structure loading should be complete

MANDATORY COMPLETION REQUIREMENTS (per sprint plan document):
1. Update Sprint 2 Completion Notes section in PICKLIST_ENHANCEMENT_SPRINT_PLAN.md using Edit tool
2. Follow exact template in "Document Update Process" section
3. Include specific changes, code locations, challenges, context for Sprint 3
4. Update "Last Updated" field at bottom of document
5. Verify all Sprint 2 Success Criteria are met before marking complete

FAILURE TO FOLLOW THESE INSTRUCTIONS WILL BREAK PROJECT COORDINATION.

START IMPLEMENTATION.
```

### Sprint 2 Success Criteria
- [ ] PicklistAnalysisService uses unified field_selections structure
- [ ] Strategy parsing includes complete label descriptions
- [ ] GPT prompts include category groupings and data type information
- [ ] Text fields are properly recognized in strategy analysis
- [ ] Metric importance scoring uses enhanced metadata

### Sprint 2 Completion Notes
**Changes Made**:
<!-- Fill in during Sprint 2 -->

**Challenges Encountered**:
<!-- Fill in during Sprint 2 -->

**Important Context for Sprint 3**:
<!-- Fill in during Sprint 2 -->

---

## SPRINT 3: Team Data Preparation Enhancement
**Estimated Tokens**: ~13,000  
**Focus**: Update team data structure with enhanced labels and text content

### Sprint 3 Objectives
1. Enhance team data preparation with enhanced label mappings
2. Include text field data in team profiles sent to GPT
3. Update team metrics processing with proper field-to-label mapping
4. Ensure team scouting_data uses enhanced label names

### Files to Modify
- `/backend/app/services/picklist_gpt_service.py` (team data methods)
- `/backend/app/services/data_aggregation_service.py` (team aggregation)

### Key Changes Required
1. **prepare_team_data_for_gpt()**: Include enhanced field data and text content
2. **Team aggregation**: Map original field names to enhanced label names
3. **_prepare_teams_with_scores()**: Use enhanced label mappings
4. **Text data inclusion**: Add strategy_field, scout_comments to team profiles

### Copy-Paste Prompt for Sprint 3
```
CRITICAL INSTRUCTIONS: Before starting, you MUST read the entire PICKLIST_ENHANCEMENT_SPRINT_PLAN.md document first. Follow ALL instructions in the "INSTRUCTIONS FOR CONTEXT WINDOWS" section.

I need to implement Sprint 3 of the Picklist Enhancement project.

MANDATORY FIRST STEP: Read /PICKLIST_ENHANCEMENT_SPRINT_PLAN.md completely and verify Sprints 1-2 are marked as complete with proper completion notes.

CONTEXT: Sprints 1-2 updated data loading and strategy analysis. Now we need to enhance team data preparation to include enhanced labels and text content in team profiles sent to GPT.

SPRINT 3 OBJECTIVES:
1. Update prepare_team_data_for_gpt() to include enhanced field data and text content
2. Ensure team scouting_data uses enhanced label names (not original field headers)
3. Include text field data (strategy_field, scout_comments) in team profiles
4. Update team metrics processing with proper field-to-label mapping

KEY FILES TO READ FIRST:
- /PICKLIST_ENHANCEMENT_SPRINT_PLAN.md (CRITICAL: Read instructions section AND Sprint 1-2 completion notes)
- /backend/app/services/picklist_gpt_service.py (team data preparation methods)
- /backend/app/services/data_aggregation_service.py (team aggregation)
- /backend/app/data/unified_event_2025lake.json (team data structure)

IMPLEMENTATION PRIORITY:
1. Update prepare_team_data_for_gpt() method to use enhanced labels
2. Modify team data aggregation to map field names to label names
3. Include text fields in team profiles sent to GPT
4. Update _prepare_teams_with_scores() with enhanced mappings

DEPENDENCIES FROM PREVIOUS SPRINTS (verify in sprint plan document):
- Enhanced label loading (Sprint 1)
- Unified field selections loading (Sprint 1-2)
- Text field support infrastructure (Sprint 1)

MANDATORY COMPLETION REQUIREMENTS (per sprint plan document):
1. Update Sprint 3 Completion Notes section in PICKLIST_ENHANCEMENT_SPRINT_PLAN.md using Edit tool
2. Follow exact template in "Document Update Process" section
3. Include specific changes, code locations, challenges, context for Sprint 4
4. Update "Last Updated" field at bottom of document
5. Verify all Sprint 3 Success Criteria are met before marking complete

FAILURE TO FOLLOW THESE INSTRUCTIONS WILL BREAK PROJECT COORDINATION.

START IMPLEMENTATION.
```

### Sprint 3 Success Criteria
- [ ] Team data uses enhanced label names throughout
- [ ] Text fields (strategy notes, comments) included in team profiles
- [ ] Field-to-label mapping works correctly in team aggregation
- [ ] GPT receives complete team data with enhanced context
- [ ] Team metrics include label descriptions and metadata

### Sprint 3 Completion Notes
**Changes Made**:
<!-- Fill in during Sprint 3 -->

**Challenges Encountered**:
<!-- Fill in during Sprint 3 -->

**Important Context for Sprint 4**:
<!-- Fill in during Sprint 3 -->

---

## SPRINT 4: API Integration & Final Validation
**Estimated Tokens**: ~10,000  
**Focus**: Update API endpoints and validate complete integration

### Sprint 4 Objectives
1. Update picklist API endpoints to use enhanced data structure
2. Ensure API responses include enhanced labels and metadata
3. Add validation for enhanced data structure integrity
4. Test complete integration from strategy input to picklist output

### Files to Modify
- `/backend/app/api/picklist_generator.py`
- `/backend/app/api/picklist_analysis.py`

### Key Changes Required
1. **API endpoint updates**: Ensure enhanced field selections are loaded
2. **Response format**: Include enhanced labels and metadata in API responses
3. **Data validation**: Add checks for enhanced data structure integrity
4. **Integration testing**: Verify complete pipeline functionality

### Copy-Paste Prompt for Sprint 4
```
CRITICAL INSTRUCTIONS: Before starting, you MUST read the entire PICKLIST_ENHANCEMENT_SPRINT_PLAN.md document first. Follow ALL instructions in the "INSTRUCTIONS FOR CONTEXT WINDOWS" section.

I need to implement Sprint 4 of the Picklist Enhancement project.

MANDATORY FIRST STEP: Read /PICKLIST_ENHANCEMENT_SPRINT_PLAN.md completely and verify Sprints 1-3 are marked as complete with proper completion notes.

CONTEXT: Sprints 1-3 updated core services to use enhanced labels and text content. Now we need to update API endpoints and validate the complete integration.

SPRINT 4 OBJECTIVES:
1. Update picklist API endpoints to use enhanced data structure
2. Ensure API responses include enhanced labels and metadata
3. Add validation for enhanced data structure integrity
4. Test complete integration from strategy input to picklist output

KEY FILES TO READ FIRST:
- /PICKLIST_ENHANCEMENT_SPRINT_PLAN.md (CRITICAL: Read instructions section AND Sprint 1-3 completion notes)
- /backend/app/api/picklist_generator.py (current API endpoints)
- /backend/app/api/picklist_analysis.py (strategy analysis endpoints)
- Enhanced service implementations from previous sprints

IMPLEMENTATION PRIORITY:
1. Update API endpoints to use enhanced services
2. Modify response formats to include enhanced metadata
3. Add data validation and error handling
4. Test strategy parsing → picklist generation pipeline

DEPENDENCIES FROM PREVIOUS SPRINTS (verify in sprint plan document):
- Enhanced data loading (Sprint 1)
- Improved strategy analysis (Sprint 2)  
- Enhanced team data preparation (Sprint 3)

VALIDATION CHECKLIST:
- Strategy descriptions receive complete label context
- Picklist generation includes text data and enhanced labels
- API responses include proper metadata
- Backward compatibility maintained

MANDATORY COMPLETION REQUIREMENTS (per sprint plan document):
1. Update Sprint 4 Completion Notes section in PICKLIST_ENHANCEMENT_SPRINT_PLAN.md using Edit tool
2. Follow exact template in "Document Update Process" section
3. Include specific changes, code locations, challenges, final integration status
4. Update "Last Updated" field at bottom of document
5. Verify all Sprint 4 Success Criteria AND Project Completion Validation are met
6. Mark project as COMPLETE if all validation scenarios pass

FAILURE TO FOLLOW THESE INSTRUCTIONS WILL BREAK PROJECT COORDINATION.

START IMPLEMENTATION.
```

### Sprint 4 Success Criteria
- [ ] API endpoints use enhanced data structure
- [ ] Strategy analysis returns enhanced metric information
- [ ] Picklist generation includes text content and label descriptions
- [ ] Complete integration works end-to-end
- [ ] Data validation and error handling implemented

### Sprint 4 Completion Notes
**Changes Made**:
<!-- Fill in during Sprint 4 -->

**Challenges Encountered**:
<!-- Fill in during Sprint 4 -->

**Final Integration Status**:
<!-- Fill in during Sprint 4 -->

---

## PROJECT COMPLETION VALIDATION

### End-to-End Test Scenarios
1. **Strategy Input**: "Focus on teams with strong autonomous coral scoring and good strategy notes"
   - **Expected**: GPT receives enhanced label descriptions for auto_coral_* metrics
   - **Expected**: Strategy analysis recognizes text field importance

2. **Picklist Generation**: Generate picklist for team 2973
   - **Expected**: Team profiles include strategy_field and scout_comments content
   - **Expected**: Enhanced label descriptions guide GPT analysis
   - **Expected**: Text data influences team rankings appropriately

### Success Metrics
- [ ] Strategy descriptions use complete enhanced label context
- [ ] Picklist generation includes text data from unified structure
- [ ] Enhanced labels and descriptions guide GPT analysis
- [ ] System maintains backward compatibility
- [ ] Performance remains acceptable with enhanced data

### Known Limitations
- Text field content quality depends on scouting data input
- Enhanced context increases token usage but improves analysis quality
- Label mapping hierarchy requires proper data structure maintenance

---

## MAINTENANCE NOTES

### Data Structure Dependencies
- **Field Selections**: Must maintain label_mapping structure with complete metadata
- **Game Labels**: Serves as fallback when field selections incomplete
- **Unified Dataset**: Team scouting_data must use consistent field naming

### Future Enhancements
- Dynamic label discovery based on data patterns
- Advanced text field analysis for strategy pattern recognition
- Label quality scoring and validation automation

### Troubleshooting Guide
- **Missing Labels**: Check field_selections → game_labels → fallback hierarchy
- **Text Field Issues**: Verify data_type:"text" in label definitions
- **Performance**: Monitor token usage with enhanced context
- **Compatibility**: Ensure fallbacks work when enhanced data unavailable

---

**Document Status**: Sprint 1 Complete - Ready for Sprint 2  
**Last Updated**: July 6, 2025  
**Next Action**: Execute Sprint 2 using provided copy-paste prompt