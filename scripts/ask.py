import urllib.request
import json
import sys

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        print("\n" + "=" * 60)
        print("🤖 ENTERPRISE RAG CHATBOT (Ask anything from your docs)")
        print("=" * 60)
        question = input("\n👉 Enter your question: ").strip()

    if not question:
        print("No question entered.")
        return

    print(f"\nThinking and searching documents for: '{question}' ...")
    
    url = "http://127.0.0.1:8000/query"
    payload = json.dumps({"query": question}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        response = urllib.request.urlopen(req, timeout=30)
        data = json.loads(response.read().decode("utf-8"))
        
        status = data.get("status")
        conf = data.get("confidence")
        
        print("\n" + "-" * 60)
        if status == "answered":
            print(f"✅ STATUS:     ANSWERED (Confidence: {conf})")
            print(f"\n💬 ANSWER:\n{data.get('answer')}\n")
            sources = data.get("sources", [])
            if sources:
                print("📚 CITATION SOURCES:")
                for idx, s in enumerate(sources, 1):
                    print(f"  [{idx}] {s.get('doc_name')} (Page {s.get('page_num')})")
                    print(f"      Excerpt: \"{s.get('snippet')}\"")
        elif status == "refused":
            print(f"🛡️ STATUS:     REFUSED (Confidence: {conf})")
            print(f"⚠️ REASON:     {data.get('reason')}")
            print("💡 The evidence in your uploaded documents is insufficient to answer this safely.")
        else:
            print(f"❌ STATUS:     ERROR")
            print(f"⚠️ REASON:     {data.get('reason')}")
        print("-" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Could not reach server at {url}: {e}")
        print("Make sure the server is running with: python run_server.py\n")

if __name__ == "__main__":
    main()
