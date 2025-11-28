// =============================================================================
// CDI Analysis Types
// =============================================================================

export interface DocumentationGap {
  gap_type: 'specificity' | 'acuity' | 'comorbidity' | 'medical_necessity';
  condition: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  suggested_query?: string;
  clinical_indicators?: string[];
}

export interface ClinicalEntity {
  text: string;
  type: string;
  confidence: number;
  icd10_codes?: Array<{ code: string; description: string }>;
  negated?: boolean;
  historical?: boolean;
}

export interface CodingSuggestion {
  code: string;
  code_system: 'ICD-10-CM' | 'ICD-10-PCS' | 'CPT' | 'HCPCS';
  description: string;
  confidence: number;
  rationale: string;
  supporting_evidence?: string[];
}

export interface NoteAnalysisResult {
  summary: string;
  documentation_gaps: DocumentationGap[];
  clinical_entities: ClinicalEntity[];
  coding_suggestions: CodingSuggestion[];
  overall_completeness_score: number;
  processing_time_ms?: number;
}

export interface CDIQueryResult {
  query: string;
  gap_type: string;
  condition: string;
  query_style: 'open_ended' | 'yes_no' | 'documentation_based';
  compliance_notes: string[];
  documentation_requirements: string[];
}

export interface CDIGuideline {
  condition: string;
  icd10_codes: string[];
  documentation_requirements: string[];
  specificity_elements: string[];
  common_gaps: string[];
  query_templates: string[];
  clinical_indicators: string[];
  severity_levels?: string[];
}

// =============================================================================
// Revenue Optimization Types
// =============================================================================

export interface EMAnalysis {
  recommended_level: string;
  em_code: string;
  current_level?: string;
  rationale: string;
  documentation_supports: string[];
  mdm_complexity: string;
  mdm_analysis?: {
    problems_addressed: string;
    data_reviewed: string;
    risk_level: string;
    overall_complexity: string;
  };
  time_based_option?: {
    total_time: number;
    supports_level: string;
    activities: string[];
  };
}

export interface HCCOpportunity {
  condition: string;
  hcc_code: string;
  raf_value: number;
  documentation_status: 'documented' | 'suspected' | 'missing';
  suggested_query?: string;
  clinical_indicators?: string[];
}

export interface DRGAnalysis {
  predicted_drg: string;
  drg_description?: string;
  drg_weight: number;
  mcc_present: boolean;
  cc_present: boolean;
  optimization_opportunities: string[];
}

export interface CodingRecommendation {
  code: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  rationale: string;
}

export interface RevenueAnalysisResult {
  summary: string;
  estimated_revenue_impact: number;
  em_analysis?: EMAnalysis;
  hcc_opportunities?: HCCOpportunity[];
  drg_analysis?: DRGAnalysis;
  coding_recommendations: CodingRecommendation[];
}

export interface HCCCode {
  hcc_code: string;
  hcc_description: string;
  icd10_code: string;
  icd10_description: string;
  raf_value: number;
  hierarchy_notes?: string;
}

export interface HCCAnalysisResult {
  model_version: string;
  total_raf_score: number;
  hcc_codes: HCCCode[];
  hierarchies_applied: string[];
  estimated_annual_value: number;
  opportunities?: Array<{
    condition: string;
    potential_hcc: string;
    raf_value: number;
    clinical_indicators: string[];
  }>;
}

export interface Investigation {
  name: string;
  type: 'laboratory' | 'imaging' | 'procedure' | 'consultation';
  priority: 'stat' | 'urgent' | 'routine';
  rationale: string;
  expected_findings: string[];
  cpt_codes?: string[];
}

export interface InvestigationResult {
  condition: string;
  severity_assessment: string;
  recommended_investigations: Investigation[];
  clinical_pathway: string;
  documentation_tips: string[];
}

// =============================================================================
// Quality Measures Types
// =============================================================================

export interface HEDISMeasureResult {
  measure_id: string;
  measure_name: string;
  status: 'met' | 'not_met' | 'exclusion' | 'pending';
  eligible: boolean;
  documentation_found: string[];
  gaps: string[];
  suggested_actions: string[];
  query?: string;
}

export interface HEDISEvaluationResult {
  patient_summary: string;
  total_measures_evaluated: number;
  measures_met: number;
  measures_not_met: number;
  exclusions: number;
  measure_results: HEDISMeasureResult[];
  overall_compliance_rate: number;
  priority_actions: string[];
}

export interface HEDISMeasure {
  measure_id: string;
  measure_name: string;
  domain: string;
  description: string;
  eligible_population: string;
  numerator: string;
  denominator: string;
  exclusions: string[];
  data_sources: string[];
  reporting_year: number;
}

// =============================================================================
// History Types
// =============================================================================

export interface CDIHistoryItem {
  id: string;
  created_at: string;
  clinical_note_excerpt: string;
  query_type: 'analysis' | 'query_generation' | 'gap_detection';
  gap_type?: string;
  condition?: string;
  generated_query?: string;
  gaps_found?: number;
  completeness_score?: number;
}

export interface QualityHistoryItem {
  id: string;
  created_at: string;
  patient_age: number;
  patient_gender: string;
  total_measures: number;
  measures_met: number;
  measures_not_met: number;
  compliance_rate: number;
  priority_gaps: string[];
}
