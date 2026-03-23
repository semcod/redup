"""Test fuzzy similarity detection for HTML/CSS components."""

import tempfile
from pathlib import Path

from redup.core.fuzzy_similarity import FuzzySimilarityDetector
from redup.core.scanner import CodeBlock


def test_html_fuzzy_similarity():
    """Test fuzzy similarity detection for HTML components."""
    
    # Create test HTML blocks with similar functionality but different structure
    html_form1 = CodeBlock(
        file="login1.html",
        line_start=1,
        line_end=10,
        text="""<form class="auth-form" method="post">
    <input name="email" type="email" placeholder="Email">
    <input name="password" type="password" placeholder="Password">
    <button type="submit">Login</button>
</form>""",
        function_name="<form>"
    )
    
    html_form2 = CodeBlock(
        file="login2.html", 
        line_start=1,
        line_end=10,
        text="""<div class="panel-login">
    <form action="/login" method="POST">
        <input type="email" name="username" placeholder="Enter email">
        <input type="password" name="pass" placeholder="Enter password">
        <button class="btn btn-primary">Sign In</button>
    </form>
</div>""",
        function_name="<form>"
    )
    
    html_card1 = CodeBlock(
        file="card1.html",
        line_start=1,
        line_end=8,
        text="""<div class="card">
    <div class="card-header">Title</div>
    <div class="card-body">Content here</div>
</div>""",
        function_name="<div>"
    )
    
    html_card2 = CodeBlock(
        file="card2.html",
        line_start=1,
        line_end=8,
        text="""<section class="panel">
    <header class="panel-title">Heading</header>
    <main class="panel-content">Body content</main>
</section>""",
        function_name="<section>"
    )
    
    # Test similarity detection
    detector = FuzzySimilarityDetector(similarity_threshold=0.5)  # Lower threshold for testing
    
    # Debug: Test individual signature extraction
    print("Debug: Extracting signatures...")
    sig1 = detector.html_extractor.extract_component_signature(html_form1)
    sig2 = detector.html_extractor.extract_component_signature(html_form2)
    sig3 = detector.html_extractor.extract_component_signature(html_card1)
    sig4 = detector.html_extractor.extract_component_signature(html_card2)
    
    print(f"Form1 signature: {sig1}")
    print(f"Form2 signature: {sig2}")
    print(f"Card1 signature: {sig3}")
    print(f"Card2 signature: {sig4}")
    
    if sig1 and sig2:
        similarity = detector._compute_similarity(sig1, sig2)
        print(f"Form1 vs Form2 similarity: {similarity}")
    
    if sig3 and sig4:
        similarity = detector._compute_similarity(sig3, sig4)
        print(f"Card1 vs Card2 similarity: {similarity}")
    
    # Test with similar forms
    similar_forms = detector.find_similar_components([html_form1, html_form2])
    print(f"Similar forms found: {len(similar_forms)}")
    for block1, block2, similarity in similar_forms:
        print(f"  {block1.file} ↔ {block2.file}: {similarity:.2f}")
    
    # Test with similar cards
    similar_cards = detector.find_similar_components([html_card1, html_card2])
    print(f"Similar cards found: {len(similar_cards)}")
    for block1, block2, similarity in similar_cards:
        print(f"  {block1.file} ↔ {block2.file}: {similarity:.2f}")
    
    # Test with all blocks
    all_blocks = [html_form1, html_form2, html_card1, html_card2]
    all_similar = detector.find_similar_components(all_blocks)
    print(f"All similar components: {len(all_similar)}")
    for block1, block2, similarity in all_similar:
        print(f"  {block1.file} ↔ {block2.file}: {similarity:.2f}")


def test_css_fuzzy_similarity():
    """Test fuzzy similarity detection for CSS components."""
    
    # Create test CSS blocks with similar styles
    css_button1 = CodeBlock(
        file="button1.css",
        line_start=1,
        line_end=6,
        text="""btn-primary {
    background-color: #007bff;
    color: white;
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
}""",
        function_name="btn-primary"
    )
    
    css_button2 = CodeBlock(
        file="button2.css",
        line_start=1,
        line_end=6,
        text=""".btn-secondary {
    background: #0056b3;
    color: #ffffff;
    padding: 10px 18px;
    border: 0px;
    border-radius: 5px;
}""",
        function_name=".btn-secondary"
    )
    
    css_card1 = CodeBlock(
        file="card1.css",
        line_start=1,
        line_end=5,
        text=""".card {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
}""",
        function_name=".card"
    )
    
    css_card2 = CodeBlock(
        file="card2.css",
        line_start=1,
        line_end=5,
        text=""".panel {
    background-color: white;
    border: 1px solid #cccccc;
    border-radius: 10px;
    padding: 20px;
}""",
        function_name=".panel"
    )
    
    # Test similarity detection with lower threshold
    detector = FuzzySimilarityDetector(similarity_threshold=0.4)  # Lower threshold for testing
    
    # Debug: Test individual signature extraction
    print("Debug: Extracting CSS signatures...")
    sig1 = detector.css_extractor.extract_component_signature(css_button1)
    sig2 = detector.css_extractor.extract_component_signature(css_button2)
    sig3 = detector.css_extractor.extract_component_signature(css_card1)
    sig4 = detector.css_extractor.extract_component_signature(css_card2)
    
    print(f"Button1 signature: {sig1}")
    print(f"Button2 signature: {sig2}")
    print(f"Card1 signature: {sig3}")
    print(f"Card2 signature: {sig4}")
    
    if sig1 and sig2:
        similarity = detector._compute_similarity(sig1, sig2)
        print(f"Button1 vs Button2 similarity: {similarity}")
    
    if sig3 and sig4:
        similarity = detector._compute_similarity(sig3, sig4)
        print(f"Card1 vs Card2 similarity: {similarity}")
    
    # Test with similar buttons
    similar_buttons = detector.find_similar_components([css_button1, css_button2])
    print(f"Similar button styles found: {len(similar_buttons)}")
    for block1, block2, similarity in similar_buttons:
        print(f"  {block1.file} ↔ {block2.file}: {similarity:.2f}")
    
    # Test with similar cards
    similar_cards = detector.find_similar_components([css_card1, css_card2])
    print(f"Similar card styles found: {len(similar_cards)}")
    for block1, block2, similarity in similar_cards:
        print(f"  {block1.file} ↔ {block2.file}: {similarity:.2f}")


def test_mixed_html_css():
    """Test fuzzy detection with mixed HTML and CSS blocks."""
    
    html_form = CodeBlock(
        file="form.html",
        line_start=1,
        line_end=5,
        text="""<form class="login-form">
    <input type="email" name="email">
    <input type="password" name="password">
    <button type="submit">Login</button>
</form>""",
        function_name="<form>"
    )
    
    css_style = CodeBlock(
        file="style.css",
        line_start=1,
        line_end=4,
        text=""".login-form {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
}""",
        function_name=".login-form"
    )
    
    # HTML and CSS should not be compared with each other
    detector = FuzzySimilarityDetector(similarity_threshold=0.7)
    similar = detector.find_similar_components([html_form, css_style])
    
    print(f"Mixed HTML/CSS similar components: {len(similar)}")
    # Should be 0 since HTML and CSS are different types


if __name__ == "__main__":
    print("Testing HTML fuzzy similarity...")
    test_html_fuzzy_similarity()
    
    print("\nTesting CSS fuzzy similarity...")
    test_css_fuzzy_similarity()
    
    print("\nTesting mixed HTML/CSS...")
    test_mixed_html_css()
    
    print("\nAll tests completed!")
