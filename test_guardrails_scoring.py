"""Quick smoke test for the new 3-tier groundedness scoring."""
from guardrails import check_output_guardrail, validate_citations

# Simulate a well-grounded output with proper citations
context = [
    "Deep learning models achieve 95.2% accuracy on cardiovascular disease prediction "
    "using ECG signals. The proposed CNN-LSTM architecture outperforms traditional methods.",
    "Federated learning enables collaborative model training across hospitals without "
    "sharing patient data. The differential privacy mechanism ensures HIPAA compliance."
]

output = (
    "## Research Overview\n"
    "Deep learning models have demonstrated 95.2% accuracy in cardiovascular disease "
    "prediction using ECG signals [1]. The CNN-LSTM architecture proposed in this study "
    "shows superior performance compared to traditional methods [1]. "
    "Federated learning enables collaborative model training across hospitals "
    "without sharing patient data [2]. The differential privacy mechanism "
    "ensures HIPAA compliance [2].\n"
    "## Conclusion\n"
    "This research demonstrates significant advances in both cardiovascular prediction "
    "and privacy-preserving collaborative learning [1, 2]."
)

# Test groundedness
ok, msg, score = check_output_guardrail(output, context)
print(f"Grounded: {ok}")
print(f"Score: {score:.1%}")
print(f"Details: {msg}")
print()

# Test citation validation
sources = [{"rank": 1, "title": "ecg_paper.pdf"}, {"rank": 2, "title": "federated.pdf"}]
cit = validate_citations(output, sources)
print(f"Citations valid: {cit['valid']}")
print(f"Citation coverage: {cit['citation_coverage']:.1%}")
print(f"Total citations: {cit['total_citations']}")
print(f"Invalid citations: {cit['invalid_citations']}")
print()

# Test a poorly grounded output (hallucinated content)
bad_output = (
    "## Research Overview\n"
    "The novel XYZTransformer model achieves 99.8% accuracy on the MIMIC-IV dataset "
    "using a revolutionary quantum attention mechanism. This represents a 45% improvement "
    "over GPT-4 in clinical settings."
)
ok2, msg2, score2 = check_output_guardrail(bad_output, context)
print(f"Bad output grounded: {ok2}")
print(f"Bad output score: {score2:.1%}")
print(f"Bad output details: {msg2}")
print()

# Test a refusal response
print("--- Testing Refusal / Absence-of-evidence Response ---")
refusal_output = "Not stated in the document."
ok3, msg3, score3 = check_output_guardrail(refusal_output, context)
cit3 = validate_citations(refusal_output, sources)

print(f"Refusal Grounded: {ok3} (Score: {score3:.1%})")
print(f"Refusal details: {msg3}")
print(f"Refusal Citations Valid: {cit3['valid']}")
print(f"Refusal Citation Coverage: {cit3['citation_coverage']:.1%}")
print(f"Refusal is_refusal Flag: {cit3['is_refusal']}")
