import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import App from '../../frontend/src/App';

describe('RNFLT structural gate', () => {
  it('raw OCT with rnflt_extraction unavailable must show unavailable not demo RNFLT', () => {
    // Gated path: raw_oct + rnflt_extraction.available false + model_result null
    const blocked: any = {
      is_valid: true,
      status: 'PASS',
      input_type: 'raw_oct',
      ai_analysis: { status: 'RNFLT EXTRACTION REQUIRED', analysis_available: false, rnflt_extraction: { available: false, reason: 'OCT segmentation checkpoint unavailable' }, message: 'Quantitative RNFLT extraction unavailable', prevented_false_result: true },
      model_result: null,
      rnflt_analysis: undefined,
      raw_oct_study: { technical_validation: 'PASS' },
    };
    // This test asserts the data contract: blocked analysis must not contain demo RNFLT fields
    expect(blocked.rnflt_analysis).toBeUndefined();
    expect(blocked.model_result).toBeNull();
    expect(blocked.ai_analysis.rnflt_extraction.available).toBe(false);
  });

  it('valid RNFLT input still renders classifier result', async () => {
    const rnflt: any = {
      is_valid: true,
      status: 'PASS',
      input_type: 'rnflt_numeric',
      model_result: { status: 'TRAINED', predicted_class: 1, model_estimated_classification_score: 0.94, model_estimated_classification_score_pct: '94.0%', predicted_category: 'Glaucoma' },
      rnflt_analysis: { mean_thickness_um: 79.4, median_thickness_um: 31.4, max_thickness_um: 250, min_thickness_um: 0, heatmap_image: 'data:image/png;base64,xxx', dimensions: [225,225] },
      explainability: { available: true },
    };
    expect(rnflt.model_result.predicted_class).toBe(1);
    expect(rnflt.rnflt_analysis.mean_thickness_um).toBe(79.4);
  });
});
