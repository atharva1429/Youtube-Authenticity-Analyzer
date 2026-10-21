import json
import pandas as pd

def main():
    try:
        with open("benchmark_report.json") as f:
            before_report = json.load(f)
    except Exception as e:
        print("Could not load benchmark_report.json")
        return

    try:
        with open("benchmark_report_adapted.json") as f:
            after_report = json.load(f)
    except Exception as e:
        print("Could not load benchmark_report_adapted.json")
        return

    print("=======================================")
    print("      DOMAIN ADAPTATION COMPARISON     ")
    print("=======================================")
    
    print("\n[CHAMPION MODEL CHANGE]")
    print(f"Before: {before_report['champion_model']} (F1: {before_report['champion_f1']:.4f})")
    print(f"After:  {after_report['champion_model']} (F1: {after_report['champion_f1']:.4f})")

    champ_before = before_report["champion_model"]
    champ_after = after_report["champion_model"]
    
    print("\n[OVERALL METRICS]")
    print(f"Metrics             | Before ({champ_before[:12]}...) | After ({champ_after[:12]}...)")
    print("-" * 65)
    metrics = ["Accuracy", "F1", "ROC-AUC"]
    for m in metrics:
        b_val = before_report["models"][champ_before]["Overall"][m]
        a_val = after_report["models"][champ_after]["Overall"][m]
        print(f"{m.ljust(19)} | {b_val:.4f}              | {a_val:.4f}")
        
    print("\n[YOUTUBE_EDU FOLD METRICS]")
    print("Note: The 'Before' model never saw YouTube_Edu data.")
    print("These stats show the performance of the 'After' model specifically on YouTube_Edu fold:")
    if "YouTube_Edu" in after_report["models"][champ_after]["Per_Dataset"]:
        yt_metrics = after_report["models"][champ_after]["Per_Dataset"]["YouTube_Edu"]
        for m in metrics:
            val = yt_metrics[m]
            if val is not None:
                print(f"- {m}: {val:.4f}")
            else:
                print(f"- {m}: N/A")
    else:
        print("YouTube_Edu dataset not found in after report.")
        
    print("\n=======================================")

if __name__ == "__main__":
    main()
