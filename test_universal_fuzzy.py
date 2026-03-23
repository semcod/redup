"""Test universal fuzzy similarity detection across multiple languages and DSLs."""

import tempfile
from pathlib import Path

from redup.core.universal_fuzzy import UniversalFuzzyDetector, UniversalFuzzyExtractor
from redup.core.scanner import CodeBlock


def test_programming_languages():
    """Test fuzzy similarity across programming languages."""
    
    # JavaScript function
    js_function = CodeBlock(
        file="auth.js",
        line_start=1,
        line_end=8,
        text="""function authenticateUser(username, password) {
    if (!username || !password) {
        throw new Error('Missing credentials');
    }
    const token = generateToken(username);
    return { success: true, token };
}""",
        function_name="authenticateUser"
    )
    
    # Python function (similar functionality)
    py_function = CodeBlock(
        file="auth.py",
        line_start=1,
        line_end=8,
        text="""def authenticate_user(username, password):
    if not username or not password:
        raise ValueError('Missing credentials')
    token = generate_token(username)
    return {'success': True, 'token': token}""",
        function_name="authenticate_user"
    )
    
    # Java method (similar functionality)
    java_method = CodeBlock(
        file="Auth.java",
        line_start=1,
        line_end=10,
        text="""public AuthResult authenticateUser(String username, String password) {
    if (username == null || password == null) {
        throw new IllegalArgumentException("Missing credentials");
    }
    String token = generateToken(username);
    return new AuthResult(true, token);
}""",
        function_name="authenticateUser"
    )
    
    # Test similarity detection
    detector = UniversalFuzzyDetector(similarity_threshold=0.5)
    extractor = UniversalFuzzyExtractor()
    
    print("Testing programming languages...")
    
    # Debug: Extract signatures
    js_sig = extractor.extract_universal_signature(js_function)
    py_sig = extractor.extract_universal_signature(py_function)
    java_sig = extractor.extract_universal_signature(java_method)
    
    print(f"JS signature: {js_sig}")
    print(f"Python signature: {py_sig}")
    print(f"Java signature: {java_sig}")
    
    # Test similarities
    similar = detector.find_similar_components([js_function, py_function, java_method])
    print(f"Similar programming functions found: {len(similar)}")
    for block1, block2, similarity in similar:
        print(f"  {block1.file} ↔ {block2.file}: {similarity:.2f}")


def test_configuration_files():
    """Test fuzzy similarity across configuration files and DSLs."""
    
    # Docker configuration
    docker_config = CodeBlock(
        file="Dockerfile",
        line_start=1,
        line_end=6,
        text="""FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000""",
        function_name="FROM"
    )
    
    # Nginx configuration
    nginx_config = CodeBlock(
        file="nginx.conf",
        line_start=1,
        line_end=8,
        text="""server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;
    location / {
        try_files $uri $uri/ =404;
    }
}""",
        function_name="server"
    )
    
    # YAML configuration
    yaml_config = CodeBlock(
        file="config.yaml",
        line_start=1,
        line_end=8,
        text="""server:
  host: localhost
  port: 3000
  database:
    host: db
    port: 5432
    name: appdb
logging:
  level: info""",
        function_name="server"
    )
    
    # Test similarity detection
    detector = UniversalFuzzyDetector(similarity_threshold=0.4)
    extractor = UniversalFuzzyExtractor()
    
    print("\nTesting configuration files...")
    
    # Debug: Extract signatures
    docker_sig = extractor.extract_universal_signature(docker_config)
    nginx_sig = extractor.extract_universal_signature(nginx_config)
    yaml_sig = extractor.extract_universal_signature(yaml_config)
    
    print(f"Docker signature: {docker_sig}")
    print(f"Nginx signature: {nginx_sig}")
    print(f"YAML signature: {yaml_sig}")
    
    # Test similarities
    similar = detector.find_similar_components([docker_config, nginx_config, yaml_config])
    print(f"Similar config sections found: {len(similar)}")
    for block1, block2, similarity in similar:
        print(f"  {block1.file} ↔ {block2.file}: {similarity:.2f}")


def test_data_formats():
    """Test fuzzy similarity across data formats."""
    
    # JSON schema
    json_schema = CodeBlock(
        file="schema.json",
        line_start=1,
        line_end=8,
        text="""{
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"}
    },
    "required": ["id", "name"]
}""",
        function_name="{"
    )
    
    # YAML schema
    yaml_schema = CodeBlock(
        file="schema.yaml",
        line_start=1,
        line_end=8,
        text="""type: object
properties:
  id:
    type: integer
  name:
    type: string
  email:
    type: string
    format: email
required:
  - id
  - name""",
        function_name="type"
    )
    
    # Test similarity detection
    detector = UniversalFuzzyDetector(similarity_threshold=0.6)
    extractor = UniversalFuzzyExtractor()
    
    print("\nTesting data formats...")
    
    # Debug: Extract signatures
    json_sig = extractor.extract_universal_signature(json_schema)
    yaml_sig = extractor.extract_universal_signature(yaml_schema)
    
    print(f"JSON signature: {json_sig}")
    print(f"YAML signature: {yaml_sig}")
    
    # Test similarities
    similar = detector.find_similar_components([json_schema, yaml_schema])
    print(f"Similar data schemas found: {len(similar)}")
    for block1, block2, similarity in similar:
        print(f"  {block1.file} ↔ {block2.file}: {similarity:.2f}")


def test_query_languages():
    """Test fuzzy similarity across query languages."""
    
    # SQL query
    sql_query = CodeBlock(
        file="users.sql",
        line_start=1,
        line_end=4,
        text="""SELECT id, name, email 
FROM users 
WHERE active = true 
ORDER BY created_at DESC""",
        function_name="SELECT"
    )
    
    # GraphQL query
    graphql_query = CodeBlock(
        file="users.graphql",
        line_start=1,
        line_end=6,
        text="""query GetActiveUsers {
  users(where: { active: true }) {
    id
    name
    email
  }
}""",
        function_name="query"
    )
    
    # Test similarity detection
    detector = UniversalFuzzyDetector(similarity_threshold=0.5)
    extractor = UniversalFuzzyExtractor()
    
    print("\nTesting query languages...")
    
    # Debug: Extract signatures
    sql_sig = extractor.extract_universal_signature(sql_query)
    graphql_sig = extractor.extract_universal_signature(graphql_query)
    
    print(f"SQL signature: {sql_sig}")
    print(f"GraphQL signature: {graphql_sig}")
    
    # Test similarities
    similar = detector.find_similar_components([sql_query, graphql_query])
    print(f"Similar queries found: {len(similar)}")
    for block1, block2, similarity in similar:
        print(f"  {block1.file} ↔ {block2.file}: {similarity:.2f}")


def test_cross_language_patterns():
    """Test detection of similar patterns across different language families."""
    
    # Authentication pattern in JavaScript
    js_auth = CodeBlock(
        file="auth.js",
        line_start=1,
        line_end=6,
        text="""function login(email, password) {
    const user = findUser(email);
    if (!user || !verifyPassword(password, user.hash)) {
        return { error: 'Invalid credentials' };
    }
    return { token: generateJWT(user) };
}""",
        function_name="login"
    )
    
    # Authentication pattern in Python
    py_auth = CodeBlock(
        file="auth.py",
        line_start=1,
        line_end=6,
        text="""def login(email, password):
    user = find_user(email)
    if not user or not verify_password(password, user.hash):
        return {'error': 'Invalid credentials'}
    return {'token': generate_jwt(user)}""",
        function_name="login"
    )
    
    # Authentication pattern in configuration (YAML)
    yaml_auth = CodeBlock(
        file="auth.yaml",
        line_start=1,
        line_end=6,
        text="""authentication:
  provider: jwt
  login_endpoint: /api/login
  credentials:
    email: required
    password: required
  token_expiry: 3600""",
        function_name="authentication"
    )
    
    # Test similarity detection
    detector = UniversalFuzzyDetector(similarity_threshold=0.3)  # Lower threshold for cross-family
    extractor = UniversalFuzzyExtractor()
    
    print("\nTesting cross-language patterns...")
    
    # Debug: Extract signatures
    js_sig = extractor.extract_universal_signature(js_auth)
    py_sig = extractor.extract_universal_signature(py_auth)
    yaml_sig = extractor.extract_universal_signature(yaml_auth)
    
    print(f"JS auth signature: {js_sig}")
    print(f"Python auth signature: {py_sig}")
    print(f"YAML auth signature: {yaml_sig}")
    
    # Test similarities
    similar = detector.find_similar_components([js_auth, py_auth, yaml_auth])
    print(f"Similar auth patterns found: {len(similar)}")
    for block1, block2, similarity in similar:
        print(f"  {block1.file} ↔ {block2.file}: {similarity:.2f}")


if __name__ == "__main__":
    print("Testing Universal Fuzzy Similarity Detection")
    print("=" * 50)
    
    test_programming_languages()
    test_configuration_files()
    test_data_formats()
    test_query_languages()
    test_cross_language_patterns()
    
    print("\nAll universal tests completed!")
