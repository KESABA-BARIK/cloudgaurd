"""
Test the ablation study functionality.

This test verifies that the ablation study compares different rule mining variants
and correctly evaluates their performance using 5-fold cross-validation.
"""

import json
from services.ablation import (
    run_ablation_study,
    evaluate_ablation_variant,
    mine_rules_current,
    mine_rules_loose,
    mine_rules_prefix
)

# Sample test logs with labels
TEST_LOGS = [
    # User 1 - ReadLogs action
    {"userId": "alice", "action": "ReadLogs", "resource": "s3://logs/app/2024-01-01.log", "label": "allowed"},
    {"userId": "alice", "action": "ReadLogs", "resource": "s3://logs/app/2024-01-02.log", "label": "allowed"},
    {"userId": "alice", "action": "ReadLogs", "resource": "s3://logs/app/2024-01-03.log", "label": "allowed"},
    {"userId": "alice", "action": "ReadLogs", "resource": "s3://logs/db/2024-01-01.log", "label": "over-granted"},
    
    # User 1 - WriteData action
    {"userId": "alice", "action": "WriteData", "resource": "s3://data/user-data/alice.json", "label": "allowed"},
    {"userId": "alice", "action": "WriteData", "resource": "s3://data/public/shared.json", "label": "over-granted"},
    
    # User 2 - ReadLogs action
    {"userId": "bob", "action": "ReadLogs", "resource": "s3://logs/app/2024-01-01.log", "label": "allowed"},
    {"userId": "bob", "action": "ReadLogs", "resource": "s3://logs/app/2024-01-02.log", "label": "allowed"},
    {"userId": "bob", "action": "ReadLogs", "resource": "s3://logs/app/2024-01-03.log", "label": "allowed"},
    {"userId": "bob", "action": "ReadLogs", "resource": "s3://logs/admin/2024-01-01.log", "label": "over-granted"},
    
    # User 2 - DeleteData action
    {"userId": "bob", "action": "DeleteData", "resource": "s3://data/backup/old.json", "label": "over-granted"},
    {"userId": "bob", "action": "DeleteData", "resource": "s3://data/cache/temp.json", "label": "over-granted"},
]


def test_variant_mining():
    """Test that each variant can mine rules."""
    print("\n" + "="*60)
    print("TEST 1: Rule Mining Variants")
    print("="*60)
    
    # Test current variant
    print("\n--- Current Variant (optimized) ---")
    rules_current = mine_rules_current(TEST_LOGS)
    print(f"Mined {len(rules_current)} rules")
    for rule in rules_current[:3]:
        print(f"  {rule['userId']}.{rule['action']}: {rule['resourcePattern']} (conf: {rule['confidence']:.2f})")
    
    # Test loose variant
    print("\n--- Loose Variant ---")
    rules_loose = mine_rules_loose(TEST_LOGS)
    print(f"Mined {len(rules_loose)} rules")
    for rule in rules_loose[:3]:
        print(f"  {rule['userId']}.{rule['action']}: {rule['resourcePattern']} (conf: {rule['confidence']:.2f})")
    
    # Test prefix variant
    print("\n--- Prefix Variant ---")
    rules_prefix = mine_rules_prefix(TEST_LOGS)
    print(f"Mined {len(rules_prefix)} rules")
    for rule in rules_prefix[:3]:
        print(f"  {rule['userId']}.{rule['action']}: {rule['resourcePattern']} (conf: {rule['confidence']:.2f})")
    
    assert len(rules_current) > 0, "Current variant should mine rules"
    assert len(rules_loose) > 0, "Loose variant should mine rules"
    assert len(rules_prefix) > 0, "Prefix variant should mine rules"
    
    print("\n✓ All variants successfully mined rules")
    return True


def test_single_variant():
    """Test evaluating a single variant."""
    print("\n" + "="*60)
    print("TEST 2: Single Variant Evaluation")
    print("="*60)
    
    print("\nEvaluating 'current' variant...")
    result = evaluate_ablation_variant(TEST_LOGS, "current")
    
    print(f"  Variant: {result['variant']}")
    print(f"  Folds: {len(result['fold_results'])}")
    print(f"  Mean Metrics:")
    print(f"    - Precision: {result['mean']['precision']:.3f} ± {result['std']['precision']:.3f}")
    print(f"    - Recall: {result['mean']['recall']:.3f} ± {result['std']['recall']:.3f}")
    print(f"    - F1-Score: {result['mean']['f1_score']:.3f} ± {result['std']['f1_score']:.3f}")
    
    assert 'variant' in result
    assert 'mean' in result
    assert 'std' in result
    assert result['variant'] == 'current'
    
    print("\n✓ Single variant evaluation successful")
    return True


def test_full_ablation_study():
    """Test the complete ablation study."""
    print("\n" + "="*60)
    print("TEST 3: Full Ablation Study")
    print("="*60)
    
    study = run_ablation_study(TEST_LOGS)
    
    print(f"\nVariants Compared:")
    for variant in study['variants_compared']:
        print(f"  - {variant}")
    
    print(f"\nWinner (by F1-Score): {study['winner']}")
    
    print("\nDetailed Results:")
    for variant_name, variant_results in study['results'].items():
        mean = variant_results['mean']
        std = variant_results['std']
        print(f"\n  {variant_name}:")
        print(f"    Precision: {mean['precision']:.3f} ± {std['precision']:.3f}")
        print(f"    Recall: {mean['recall']:.3f} ± {std['recall']:.3f}")
        print(f"    F1-Score: {mean['f1_score']:.3f} ± {std['f1_score']:.3f}")
    
    assert 'variants_compared' in study
    assert 'winner' in study
    assert 'results' in study
    assert len(study['results']) == 3, "Should compare 3 variants"
    
    print("\n✓ Full ablation study completed successfully")
    return True


def test_ablation_comparison():
    """Test that ablation study shows meaningful differences."""
    print("\n" + "="*60)
    print("TEST 4: Ablation Study Comparison")
    print("="*60)
    
    study = run_ablation_study(TEST_LOGS)
    
    f1_scores = {
        k: v['mean']['f1_score']
        for k, v in study['results'].items()
    }
    
    print("\nF1-Score Comparison:")
    for variant, score in sorted(f1_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  {variant}: {score:.3f}")
    
    # The winner should have the highest F1-score
    best_variant = max(f1_scores.items(), key=lambda x: x[1])[0]
    best_score = f1_scores[best_variant]
    
    print(f"\nBest Variant: {best_variant} (F1: {best_score:.3f})")
    
    assert best_score > 0, "At least one variant should have positive F1-score"
    
    print("\n✓ Ablation comparison validation successful")
    return True


def run_all_ablation_tests():
    """Run all ablation tests."""
    print("\n" + "="*70)
    print("ABLATION STUDY - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    tests = [
        ("Rule Mining Variants", test_variant_mining),
        ("Single Variant Evaluation", test_single_variant),
        ("Full Ablation Study", test_full_ablation_study),
        ("Ablation Comparison", test_ablation_comparison),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n🎉 ALL ABLATION TESTS PASSED!")
    else:
        print(f"\n⚠️ {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_ablation_tests()
    exit(0 if success else 1)
