"""
Lightweight sanity check — NOT an autograder.

Starts nothing itself; run your app first (docker compose up, or python app.py),
then run this in another shell:  python smoke_test.py

It checks three things against the response contract in the README:
  1. /health responds
  2. a grounded question returns an answer WITH a source
  3. an out-of-KB question DECLINES (empty sources)

Treat warnings as hints, not hard failures.
"""

import sys
import requests

BASE = "http://localhost:5000"


def ask(question):
    r = requests.post(f"{BASE}/ask", json={"question": question}, timeout=60)
    r.raise_for_status()
    return r.json()


def main():
    ok = True

    # 1. health
    try:
        h = requests.get(f"{BASE}/health", timeout=10)
        h.raise_for_status()
        print("[pass] /health responded:", h.json())
    except Exception as e:
        print("[FAIL] /health did not respond — is the app running?", e)
        sys.exit(1)

    # 2. grounded question -> answer with a source
    try:
        res = ask("How long is the return window?")
        ans, sources = res.get("answer", ""), res.get("sources", [])
        print("\nQ: How long is the return window?")
        print("   answer :", ans)
        print("   sources:", sources)
        if sources:
            print("[pass] grounded question returned at least one source")
        else:
            print("[warn] expected a non-empty 'sources' for a covered question")
            ok = False
        if "30" not in str(ans):
            print("[warn] answer didn't mention the 30-day window — check grounding")
    except Exception as e:
        print("[FAIL] grounded question errored:", e)
        ok = False

    # 3. out-of-KB question -> declines (empty sources)
    try:
        res = ask("Do you offer a student discount?")
        ans, sources = res.get("answer", ""), res.get("sources", [])
        print("\nQ: Do you offer a student discount?  (not in the KB)")
        print("   answer :", ans)
        print("   sources:", sources)
        if not sources:
            print("[pass] out-of-KB question declined (empty sources)")
        else:
            print("[warn] expected empty 'sources' — the guardrail may be leaking")
            ok = False
    except Exception as e:
        print("[FAIL] out-of-KB question errored:", e)
        ok = False

    print("\n" + ("All core checks passed." if ok else "Some checks need a look (see above)."))


if __name__ == "__main__":
    main()
