<script lang="ts">
  import '../../app.css';
</script>

<svelte:head>
  <link rel="canonical" href="https://marie.aaryandehade.com/about" />
  <title>About MARIE — Credits and origins</title>
  <meta name="description" content="MARIE’s educational architecture comes from Linda Null and Julia Lobur’s The Essentials of Computer Organization and Architecture. Learn about its origins and this simulator." />
</svelte:head>

<a class="skip-link" href="#main-content">Skip to content</a>
<div class="family-backdrop" aria-hidden="true"></div>
<header class="site-header">
  <a class="brand" href="/" aria-label="MARIE home"><img src="/ad-logo.png" alt="AD" width="34" height="34" /><span>marie<span class="orange">.</span></span></a>
  <nav aria-label="Main navigation" class="about-nav">
    <a class="nav-link" href="/">Workspace</a>
    <a class="nav-link chosen" href="/about" aria-current="page">About</a>
  </nav>
</header>

<main id="main-content" class="about-page">
  <h1>About MARIE<span class="orange">.</span></h1>
  <p class="about-lead">A small teaching computer for learning how instructions, registers, and memory work together.</p>

  <section class="panel about-section" aria-labelledby="origins">
    <h2 id="origins">The original architecture</h2>
    <p>MARIE stands for <strong>Machine Architecture that is Really Intuitive and Easy</strong>. The architecture was introduced by <strong>Linda Null and Julia Lobur</strong> in their textbook <cite>The Essentials of Computer Organization and Architecture</cite>.</p>
    <p>Credit for MARIE’s original educational architecture belongs to Null and Lobur. Their model gives students a compact way to explore assembly language and the steps a computer takes to execute a program.</p>
    <a class="about-source" href="https://h3turing.cs.hbg.psu.edu/mspapers/sources/julia-lobur.pdf" target="_blank" rel="noreferrer">Read the original MARIE simulator guide ↗</a>
  </section>

  <section class="panel about-section" aria-labelledby="implementation">
    <h2 id="implementation">This simulator</h2>
    <p>This web simulator was built by <a href="https://apps.aaryandehade.com">Aaryan Dehade</a>. It implements MARIE’s teaching architecture with an assembly editor, step-by-step execution, registers, memory inspection, and numeric input and output.</p>
    <p>This is an independent implementation. The original architecture and textbook are the work of Linda Null and Julia Lobur.</p>
    <a class="about-source" href="https://github.com/dehadeaaryan/marie-simulator" target="_blank" rel="noreferrer">View this simulator’s source code ↗</a>
  </section>

  <a class="about-back" href="/">← Back to the simulator</a>
  <footer><span>Made by <a href="https://apps.aaryandehade.com">Aaryan<span class="orange">.</span></a></span><a href="https://github.com/dehadeaaryan/marie-simulator" target="_blank" rel="noreferrer">Source code ↗</a></footer>
</main>
