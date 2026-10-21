"""
Rule-based Heuristic Analyzer Engine for CodeSentinel AI.
Detects common security vulnerabilities (OWASP Top 10), performance bottlenecks,
secret leaks, and code smells across Python, JavaScript/TypeScript, Java, Go, SQL, etc.
"""
import re
from typing import List, Dict, Any

PATTERNS = [
    # --- Critical Security Vulnerabilities ---
    {
        "id": "SEC-001",
        "category": "security",
        "severity": "critical",
        "title": "Hardcoded Secret / API Token Detected",
        "regex": r"""(?i)(?:api_key|apikey|secret|password|passwd|auth_token|access_token|private_key|aws_secret_access_key)\s*=\s*['"][a-zA-Z0-9_\-\.]{8,}['"]""",
        "description": "Hardcoded credentials or API keys committed to source control pose a severe security vulnerability. Secrets can be extracted from git history.",
        "suggestion": "Extract secrets into environment variables (e.g., os.getenv('API_KEY') or process.env.API_KEY) and store them in a secure vault or .env file excluded from git."
    },
    {
        "id": "SEC-002",
        "category": "security",
        "severity": "critical",
        "title": "Potential SQL Injection via String Interpolation",
        "regex": r"""(?i)(?:execute|cursor\.execute|query)\s*\(\s*(?:f['"]|['"].*?%|['"].*?\+|.*?\.format\().*?(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)""",
        "description": "SQL query is constructed using dynamic string formatting or concatenation with user-controlled input, allowing attackers to manipulate queries.",
        "suggestion": "Use parameterized queries / prepared statements (e.g. cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,)))."
    },
    {
        "id": "SEC-003",
        "category": "security",
        "severity": "critical",
        "title": "Command Injection Risk (shell=True or system/exec)",
        "regex": r"""(?i)(?:subprocess\.(?:Popen|run|call)\s*\(.*?shell\s*=\s*True|os\.system\s*\(|child_process\.exec\s*\(|Runtime\.getRuntime\(\)\.exec\()""",
        "description": "Invoking a system shell with dynamic commands can allow arbitrary remote code execution (RCE) if input contains unescaped shell metacharacters.",
        "suggestion": "Avoid shell=True. Pass commands as an array of arguments (e.g. subprocess.run(['ls', '-la']) without shell=True) and sanitize all inputs."
    },
    {
        "id": "SEC-004",
        "category": "security",
        "severity": "critical",
        "title": "Use of Insecure Hash Function (MD5 / SHA-1) for Security",
        "regex": r"""(?i)(?:hashlib\.md5\s*\(|hashlib\.sha1\s*\(|crypto\.createHash\s*\(\s*['"](?:md5|sha1)['"]|MessageDigest\.getInstance\s*\(\s*['"](?:MD5|SHA-1)['"])""",
        "description": "MD5 and SHA-1 are cryptographically broken and vulnerable to collision attacks. They must never be used for password hashing, digital signatures, or integrity checks.",
        "suggestion": "For password storage, use argon2, bcrypt, or scrypt. For cryptographic integrity, use SHA-256 or SHA-512 with HMAC."
    },
    {
        "id": "SEC-005",
        "category": "security",
        "severity": "high",
        "title": "Unsafe Dynamic Code Evaluation (eval / exec)",
        "regex": r"""\b(?:eval|exec)\s*\(.*?\b""",
        "description": "Evaluating dynamic strings with eval() or exec() allows untrusted code to run with full application privileges.",
        "suggestion": "Replace eval() with structured parsers such as json.loads() or ast.literal_eval() for safe data deserialization."
    },
    {
        "id": "SEC-006",
        "category": "security",
        "severity": "high",
        "title": "Cross-Site Scripting (XSS) via dangerouslySetInnerHTML or innerHTML",
        "regex": r"""(?i)(?:dangerouslySetInnerHTML|innerHTML\s*=|\$\(.*?\.html\()""",
        "description": "Directly assigning unsanitized HTML or user input to innerHTML creates client-side XSS vulnerabilities.",
        "suggestion": "Use safe DOM text properties like textContent or innerText, or sanitize HTML through DOMPurify before rendering."
    },

    # --- Performance Bottlenecks ---
    {
        "id": "PERF-001",
        "category": "performance",
        "severity": "medium",
        "title": "Potential N+1 Query in Loop",
        "regex": r"""(?i)for\s+.*?:.*?\n\s+.*?(?:db\.|cursor\.execute|session\.query|\.find|\.findById)""",
        "description": "Executing database queries inside an iteration loop leads to the classic N+1 query problem, severely degrading database performance.",
        "suggestion": "Batch queries using SQL IN clause, JOINs, or eager loading (e.g., .includes() or .options(joinedload()))."
    },
    {
        "id": "PERF-002",
        "category": "performance",
        "severity": "medium",
        "title": "Memory Leak: Missing Dependency Array or Cleanup in useEffect",
        "regex": r"""useEffect\s*\(\s*\(\s*\)\s*=>\s*\{[^}]*setInterval|useEffect\s*\(\s*\(\s*\)\s*=>\s*\{[^}]*addEventListener""",
        "description": "Setting up intervals, subscriptions, or event listeners in useEffect without returning a cleanup function causes cumulative memory leaks.",
        "suggestion": "Always return a cleanup function from useEffect (e.g., return () => clearInterval(intervalId);)."
    },
    {
        "id": "PERF-003",
        "category": "performance",
        "severity": "low",
        "title": "Synchronous File I/O in Async / Server Route",
        "regex": r"""\b(?:fs\.readFileSync|fs\.writeFileSync|time\.sleep)\b""",
        "description": "Blocking synchronous calls block the single-threaded Node.js event loop or Python async event loop, reducing overall throughput.",
        "suggestion": "Use asynchronous non-blocking alternatives (e.g. fs.promises.readFile or asyncio.sleep)."
    },

    # --- Architecture & Code Quality ---
    {
        "id": "ARCH-001",
        "category": "architecture",
        "severity": "medium",
        "title": "Unhandled Error / Empty Catch Block (Swallowed Exception)",
        "regex": r"""(?i)(?:except.*?:|\bcatch\s*\(.*?\)\s*\{)\s*(?:pass|//\s*TODO|\s*\}|\s*\n\s*pass)""",
        "description": "Catching exceptions without logging or re-throwing hides critical runtime failures, making debugging and auditing impossible.",
        "suggestion": "Log the exception with stack trace (logger.exception() or console.error()) and gracefully return an appropriate error response."
    },
    {
        "id": "ARCH-002",
        "category": "architecture",
        "severity": "medium",
        "title": "Potential Race Condition in Concurrency Operation",
        "regex": r"""(?i)(?:balance\s*=\s*balance\s*[\+\-]|user\.wallet_amount\s*[-+]=)""",
        "description": "Modifying financial or shared state without an atomic database transaction or mutex lock can cause race conditions under high concurrent load.",
        "suggestion": "Use database atomic updates (e.g. UPDATE accounts SET balance = balance - 100 WHERE id = 1 AND balance >= 100) or distributed locking (e.g. Redis Redlock)."
    },
    {
        "id": "ARCH-003",
        "category": "style",
        "severity": "low",
        "title": "Debug Logging Left in Production Code",
        "regex": r"""\b(?:print\s*\(|console\.log\s*\()""",
        "description": "Console debug statements left in production code can clutter logs and inadvertently leak sensitive customer data.",
        "suggestion": "Replace with a structured logging library (e.g. Python logging or Winston/Pino) with appropriate log levels (DEBUG/INFO/ERROR)."
    }
]

def scan_code_with_rules(code: str, file_path: str = "code.py") -> List[Dict[str, Any]]:
    """Runs regex and heuristic patterns over the given code and returns issues."""
    issues = []
    lines = code.split("\n")

    for pattern in PATTERNS:
        regex = re.compile(pattern["regex"], re.MULTILINE)
        
        for line_idx, line in enumerate(lines, 1):
            if regex.search(line):
                # Avoid duplicates on the same line for same id
                if not any(i["line_number"] == line_idx and i["rule_id"] == pattern["id"] for i in issues):
                    issues.append({
                        "file_path": file_path,
                        "line_number": line_idx,
                        "rule_id": pattern["id"],
                        "category": pattern["category"],
                        "severity": pattern["severity"],
                        "title": pattern["title"],
                        "description": pattern["description"],
                        "suggestion": pattern["suggestion"],
                        "code_snippet": line.strip()
                    })
                    
    # Also check multi-line patterns on the whole text
    multi_patterns = [p for p in PATTERNS if r"\n" in p["regex"]]
    for pattern in multi_patterns:
        regex = re.compile(pattern["regex"], re.MULTILINE | re.DOTALL)
        for match in regex.finditer(code):
            start_pos = match.start()
            line_idx = code[:start_pos].count("\n") + 1
            if not any(i["line_number"] == line_idx and i["rule_id"] == pattern["id"] for i in issues):
                matched_line = lines[line_idx - 1] if line_idx <= len(lines) else ""
                issues.append({
                    "file_path": file_path,
                    "line_number": line_idx,
                    "rule_id": pattern["id"],
                    "category": pattern["category"],
                    "severity": pattern["severity"],
                    "title": pattern["title"],
                    "description": pattern["description"],
                    "suggestion": pattern["suggestion"],
                    "code_snippet": matched_line.strip()
                })

    return issues