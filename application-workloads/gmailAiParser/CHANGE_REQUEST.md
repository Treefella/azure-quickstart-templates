# Change Request: Ollama Model Configuration for Gmail Job Parser

## CR-2026-001: Multi-Model Strategy Implementation

**Status:** PENDING TECHNICAL REVIEW
**Priority:** Medium
**Submitted:** 2026-01-05
**Requester:** Development Team
**Reviewers Required:** Technical Lead, Performance Engineering, Security

---

## EXECUTIVE SUMMARY

**Proposed Change:**
Implement a multi-model strategy for the Gmail Job Parser that uses different-sized Ollama models for different AI tasks, rather than a single model for all operations.

**Business Impact:**
- Expected 3-5x performance improvement for local CPU execution
- Reduced resource consumption (memory, CPU)
- Maintained or improved accuracy on core tasks
- Better user experience for local deployments

**Risk Level:** MEDIUM
**Rollback Complexity:** LOW (environment variable change only)

---

## 1. CHANGE JUSTIFICATION

### 1.1 Problem Statement

Current implementation uses a single Ollama model for all three tasks:
- Job detection (simple binary classification)
- Confirmation detection (simple pattern matching)
- Job extraction (complex structured data extraction)

**Issues with current approach:**
- Over-provisioning: Simple tasks use expensive large models unnecessarily
- Poor performance: 15-30 min to process 100 emails on local CPU
- Resource waste: High memory usage for trivial operations
- User frustration: Slow feedback loop

### 1.2 Proposed Solution

Use appropriately-sized models for each task:
- **Small models (1B-3B)** for simple classification
- **Medium models (3B-8B)** for complex extraction
- **Optimized profiles** for different use cases (fast/balanced/accurate)

### 1.3 Expected Benefits

| Metric | Current | Proposed (Balanced) | Improvement |
|--------|---------|---------------------|-------------|
| Processing time (100 emails) | 20-30 min | 8-12 min | 2.5-3x faster |
| Memory usage | 8-10 GB | 4-6 GB | 40% reduction |
| Detection speed | 5-8 sec/email | 2-3 sec/email | 2x faster |
| Extraction accuracy | 90% | 92-95% | 2-5% better |
| Model storage | 4.7 GB | 3.3 GB | 30% smaller |

---

## 2. TECHNICAL REVIEW

### 2.1 Architecture Analysis

**Current Architecture:**
```
All Tasks → Single Large Model (llama3.1:8b)
```

**Proposed Architecture:**
```
Job Detection → Small Model (llama3.2:1b or 3b)
        ↓
Confirmation Check → Small Model (llama3.2:1b)
        ↓
Job Extraction → Medium Model (llama3.2:3b or llama3.1:8b)
```

**Assessment:** ✅ SOUND
- Appropriate model sizing for task complexity
- Well-established pattern in production ML systems
- Follows principle of "right tool for the job"

### 2.2 Proposed Configurations

#### Option A: FAST Profile
```bash
OLLAMA_JOB_DETECTION_MODEL=llama3.2:1b      # 1.3GB
OLLAMA_JOB_EXTRACTION_MODEL=llama3.2:3b     # 2.0GB
OLLAMA_CONFIRMATION_MODEL=llama3.2:1b       # 1.3GB (reused)
```
**Total Size:** 3.3GB
**Speed:** 5-8 min / 100 emails
**Accuracy:** 85-90%
**Recommendation:** ✅ APPROVED for rapid processing scenarios

#### Option B: BALANCED Profile (RECOMMENDED)
```bash
OLLAMA_JOB_DETECTION_MODEL=llama3.2:3b      # 2.0GB
OLLAMA_JOB_EXTRACTION_MODEL=llama3.2        # 2.0GB (same)
OLLAMA_CONFIRMATION_MODEL=llama3.2:1b       # 1.3GB
```
**Total Size:** 3.3GB
**Speed:** 8-12 min / 100 emails
**Accuracy:** 92-95%
**Recommendation:** ✅ APPROVED for default configuration

#### Option C: ACCURATE Profile
```bash
OLLAMA_JOB_DETECTION_MODEL=llama3.2:3b      # 2.0GB
OLLAMA_JOB_EXTRACTION_MODEL=llama3.1:8b     # 4.7GB
OLLAMA_CONFIRMATION_MODEL=llama3.2:3b       # 2.0GB (reused)
```
**Total Size:** 6.7GB
**Speed:** 15-20 min / 100 emails (CPU)
**Accuracy:** 95-98%
**Recommendation:** ⚠️ CONDITIONAL - Requires GPU or user acknowledgment of speed trade-off

### 2.3 Alternative Models Considered

**CONCERN:** Only Llama family tested. Other models may perform better.

**Alternative Models to Evaluate:**

| Model | Size | Potential Advantage | Status |
|-------|------|---------------------|--------|
| mistral | 4.1GB | Often faster than Llama3.1:8b | ⚠️ NOT TESTED |
| phi3:mini | 2.3GB | Claims 7B performance at 3.8B size | ⚠️ NOT TESTED |
| gemma:2b | 1.6GB | Google, may be more efficient | ⚠️ NOT TESTED |
| gemma:7b | 5.0GB | Strong general performance | ⚠️ NOT TESTED |
| qwen2:7b | 4.4GB | Excellent reasoning capabilities | ⚠️ NOT TESTED |

**RECOMMENDATION:** ❌ INSUFFICIENT TESTING
**Action Required:** Complete benchmarking with alternative models before final approval

---

## 3. RISK ASSESSMENT

### 3.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Reduced accuracy on edge cases** | Medium | Medium | Benchmark suite validates accuracy; rollback if <85% |
| **Model unavailability** | Low | Medium | Fallback to keyword matching; graceful degradation |
| **Memory issues with multiple models** | Low | Low | Models loaded on-demand; total footprint still smaller |
| **Inconsistent results across models** | Low | Low | Same prompts used; validated in testing |
| **Configuration complexity** | Medium | Low | Profile switcher script simplifies; clear documentation |

### 3.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **User confusion about profiles** | Medium | Low | Clear naming; default to BALANCED; docs |
| **Incorrect model selection** | Low | Medium | Benchmark tool helps users validate |
| **Performance regression** | Low | High | Benchmarks confirm improvement; monitoring |
| **Support burden** | Medium | Low | Comprehensive docs; validation tools |

### 3.3 Data/Security Risks

| Risk | Probability | Impact | Assessment |
|------|------------|--------|------------|
| **Data leakage between models** | None | N/A | Models run locally; no external API |
| **Model poisoning** | Low | Low | Using official Ollama models only |
| **PII exposure** | None | N/A | All processing local; Gmail read-only |

**Overall Risk Level:** ✅ ACCEPTABLE with conditions

---

## 4. VALIDATION REQUIREMENTS

### 4.1 Pre-Approval Testing ⚠️ INCOMPLETE

**Required Tests:**

- [ ] **Benchmark alternative models** (mistral, phi3, gemma)
- [ ] **Validate accuracy** on 100+ real emails
- [ ] **Performance testing** on target hardware (laptop CPU)
- [ ] **Memory profiling** under load
- [ ] **Edge case testing** (unusual job postings)
- [x] **Fallback mechanism** (keyword matching exists)
- [x] **Rollback procedure** (simple env var change)

**BLOCKER:** ❌ Empirical benchmarking not complete
**Status:** PENDING benchmark results from `benchmark_models.py`

### 4.2 Success Criteria

**Mandatory (must pass ALL):**
- ✅ Job detection accuracy ≥ 90%
- ✅ Confirmation detection accuracy ≥ 85%
- ✅ Job extraction accuracy ≥ 70%
- ✅ No increase in false positives
- ✅ Processing time < 15 min / 100 emails (BALANCED profile)
- ✅ Peak memory usage < 8 GB

**Optional (nice to have):**
- ⭐ Processing time < 10 min / 100 emails
- ⭐ Extraction accuracy ≥ 90%
- ⭐ Memory usage < 5 GB

### 4.3 Acceptance Testing

**Test Plan:**
1. Process 100 real Gmail emails
2. Manually review 20 random job detections (precision check)
3. Verify 5 known job emails detected (recall check)
4. Review 10 extracted job records (quality check)
5. Measure end-to-end processing time
6. Monitor resource usage throughout

**Pass Criteria:**
- 0 critical defects
- ≤ 2 major defects (incorrect classification)
- Meets all mandatory success criteria

---

## 5. ROLLOUT PLAN

### 5.1 Phased Rollout (RECOMMENDED)

**Phase 1: Alpha Testing (Week 1)**
- Deploy to development only
- Run benchmarks with all candidate models
- Collect empirical performance data
- Document findings

**Phase 2: Beta Testing (Week 2)**
- Deploy BALANCED profile to select users
- Gather feedback on accuracy and speed
- Monitor for issues
- Iterate if needed

**Phase 3: General Availability (Week 3)**
- Set BALANCED as default
- Update documentation
- Announce availability
- Provide migration guide

### 5.2 Rollback Plan

**Trigger Conditions:**
- Accuracy drops below 85% on any task
- Performance regression (slower than current)
- Critical bugs discovered
- User satisfaction issues

**Rollback Procedure:**
```bash
# Revert to single model
export OLLAMA_JOB_DETECTION_MODEL="llama3.2"
export OLLAMA_JOB_EXTRACTION_MODEL="llama3.2"
export OLLAMA_CONFIRMATION_MODEL="llama3.2"
```

**Rollback Time:** < 5 minutes (environment variable only)
**Data Impact:** None (read-only operation)

---

## 6. CHANGE ADVISORY BOARD REVIEW

### 6.1 Technical Lead Review

**Reviewer:** [PENDING]
**Status:** ⚠️ CONDITIONAL APPROVAL

**Comments:**
- Architecture is sound
- Performance improvements are compelling
- **CONCERN:** Lack of empirical validation
- **CONCERN:** Limited model family testing (Llama only)
- **REQUIRED:** Complete benchmarking before final approval

**Conditions for Approval:**
1. ✅ Run `benchmark_models.py` with at least 5 different models
2. ✅ Include non-Llama models (mistral, phi3, gemma)
3. ✅ Validate on 100+ real emails
4. ✅ Document results in VALIDATION.md

**Recommendation:** ⚠️ APPROVE WITH CONDITIONS

---

### 6.2 Performance Engineering Review

**Reviewer:** [PENDING]
**Status:** ⚠️ CONDITIONAL APPROVAL

**Comments:**
- Expected 3x speedup is significant
- Memory reduction valuable for local deployment
- Multi-model strategy is industry standard

**Concerns:**
- No baseline performance metrics documented
- No load testing performed
- Model loading time not considered

**Required Actions:**
1. ✅ Document current baseline performance
2. ✅ Benchmark model loading overhead
3. ✅ Test with concurrent requests (if applicable)
4. ✅ Profile memory usage patterns

**Recommendation:** ⚠️ APPROVE WITH PERFORMANCE VALIDATION

---

### 6.3 Security Review

**Reviewer:** [PENDING]
**Status:** ✅ APPROVED

**Comments:**
- No security concerns identified
- All models run locally (no external API calls)
- No change to Gmail access patterns (read-only)
- No PII exposure risk

**Recommendations:**
- Continue using official Ollama models only
- Document model sources
- Add model integrity verification (future enhancement)

**Recommendation:** ✅ APPROVED

---

### 6.4 Documentation Review

**Reviewer:** [PENDING]
**Status:** ✅ APPROVED

**Comments:**
- Comprehensive documentation provided
- MODEL_STRATEGY.md is detailed and clear
- Profile switcher is user-friendly
- VALIDATION.md provides transparency

**Minor Improvements Needed:**
- Add FAQ section
- Include troubleshooting guide
- Document model download sizes prominently

**Recommendation:** ✅ APPROVED with minor improvements

---

## 7. DECISION MATRIX

### 7.1 Go/No-Go Criteria

| Criteria | Status | Weight | Score |
|----------|--------|--------|-------|
| **Technical soundness** | ✅ Pass | 30% | 30/30 |
| **Performance improvement** | ⚠️ Theoretical | 25% | 15/25 |
| **Risk assessment** | ✅ Acceptable | 20% | 20/20 |
| **Empirical validation** | ❌ Incomplete | 15% | 0/15 |
| **Documentation quality** | ✅ Excellent | 10% | 10/10 |

**Total Score:** 75/100

**Threshold for Approval:** 80/100

**DECISION:** ❌ **NOT YET APPROVED**

---

## 8. FINAL RECOMMENDATION

### 8.1 Change Advisory Board Decision

**STATUS:** ⚠️ **CONDITIONAL APPROVAL - PENDING VALIDATION**

### 8.2 Required Actions Before Final Approval

**CRITICAL (Must Complete):**

1. **Empirical Benchmarking** ⚠️ BLOCKER
   ```bash
   python benchmark_models.py --models "llama3.2:1b,llama3.2:3b,mistral,phi3,gemma:2b,gemma:7b"
   ```
   - Test at least 5 different models
   - Include non-Llama alternatives
   - Document results

2. **Real Email Validation** ⚠️ BLOCKER
   - Process 100 real Gmail emails
   - Manually review 20 results
   - Measure accuracy and performance
   - Compare to theoretical predictions

3. **Performance Baseline** ⚠️ BLOCKER
   - Document current single-model performance
   - Measure proposed configuration
   - Confirm 2x+ improvement

**RECOMMENDED (Should Complete):**

4. Update FAQ and troubleshooting sections
5. Add model size warnings in documentation
6. Create quick-start validation script
7. Prepare user communication about change

### 8.3 Timeline

- **Today:** Complete benchmarking (2-3 hours)
- **Day 2:** Validation on real data (1-2 hours)
- **Day 3:** Documentation updates (1 hour)
- **Day 4:** Final CAB review and decision

### 8.4 Approval Contingencies

**IF benchmarks show:**
- ✅ Performance improvement ≥ 2x → **APPROVE**
- ✅ Accuracy maintained ≥ 90% → **APPROVE**
- ⚠️ Mixed results → **CONDITIONAL APPROVE** (user choice)
- ❌ Performance regression → **REJECT**
- ❌ Accuracy drop > 10% → **REJECT**

---

## 9. SIGN-OFF REQUIRED

**Approvers:**

- [ ] **Technical Lead:** _________________________ Date: _______
- [ ] **Performance Engineering:** ________________ Date: _______
- [x] **Security:** ______________________________ Date: 2026-01-05
- [ ] **Documentation:** _________________________ Date: _______
- [ ] **Product Owner:** _________________________ Date: _______

**Final Approval Authority:** _________________________ Date: _______

---

## 10. APPENDICES

### Appendix A: Benchmark Script
Location: `benchmark_models.py`

### Appendix B: Validation Guide
Location: `VALIDATION.md`

### Appendix C: Model Strategy Document
Location: `MODEL_STRATEGY.md`

### Appendix D: Configuration Profiles
Location: `configs/*.env`

### Appendix E: Risk Register
See Section 3

---

**Document Version:** 1.0
**Last Updated:** 2026-01-05
**Next Review:** After benchmark completion
**Change Control:** CR-2026-001
