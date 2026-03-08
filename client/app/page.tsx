'use client'

import Link from 'next/link'
import { Github, GitBranch, FileCode, Network } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b border-border/40 backdrop-blur-sm sticky top-0 z-50 bg-background/80">
        <div className="container flex h-16 items-center justify-between px-4 mx-auto">
          <div className="flex items-center gap-2 cursor-default select-none">
            <div className="h-8 w-8 rounded-md bg-white/10 border border-white/20 flex items-center justify-center">
              <FileCode className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">CodeLens AI</span>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <Link href="#features" className=" text-xl font-medium text-muted-foreground hover:text-foreground transition-colors select-none">
              Features
            </Link>
            <Link href="#" className="text-xl font-medium text-muted-foreground hover:text-foreground transition-colors select-none">
              Integrations
            </Link>
            <Link href="#" className="text-xl font-medium text-muted-foreground hover:text-foreground transition-colors select-none">
              Changelog
            </Link>
            <Link href="#" className="text-xl font-medium text-muted-foreground hover:text-foreground transition-colors select-none">
              Pricing
            </Link>
          </nav>
          <div className="hidden md:flex items-center gap-4">
            <Link href="/auth/login">
              <Button variant="ghost" size="sm" className="text-sm font-medium text-muted-foreground hover:text-foreground select-none">
                Log In
              </Button>
            </Link>
            <Link href="/auth/login">
              <Button variant="outline" size="sm" className="rounded-full border-white/20 bg-transparent text-white hover:bg-white/10 px-5 font-medium select-none">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="flex-1 flex items-center justify-center py-20 px-4">
        <div className="container mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Text Content */}
            <div className="space-y-8 animate-slideUp">
              {/* <div className="inline-flex items-center gap-2 rounded-full bg-white/5 px-4 py-1.5 text-sm text-white/80 border border-white/10 select-none">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                V2.0 NOW LIVE
              </div> */}
              
              <h1 className="text-5xl md:text-7xl font-black leading-[1.05] tracking-tight select-none cursor-default">
                Understand
                <br />
                Any <span className="gradient-text">Codebase</span>
                <br />
                in Minutes.
              </h1>
              
              <p className="text-xl text-muted-foreground max-w-xl leading-relaxed select-none">
                Instantly map dependencies, explain complex logic,
                and generate documentation for any repository using
                advanced LLMs optimized for code.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/auth/login">
                  <Button size="lg" className="gap-2 text-base h-12 px-8 rounded-full">
                    <Github className="h-5 w-5" />
                    Get Started
                  </Button>
                </Link>
                <Link href="#features">
                  <Button size="lg" variant="outline" className="h-12 px-8 rounded-full border-white/20 bg-transparent text-white hover:bg-white/10">
                    Learn More
                  </Button>
                </Link>
              </div>

              {/* <div className="flex items-center gap-8 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <div className="flex -space-x-2">
                    {[1, 2, 3, 4].map((i) => (
                      <div key={i} className="w-8 h-8 rounded-full bg-zinc-700 border-2 border-background flex items-center justify-center text-xs font-medium text-white/60">
                        {i === 4 ? '+' : ''}
                      </div>
                    ))}
                  </div>
                  <span>Joined by 2,000+ developers</span>
                </div>
              </div> */}
            </div>

            {/* Right: Visual/Screenshot */}
            <div className="relative lg:block">
              <div className="relative rounded-xl border border-white/[0.08] bg-[#0d1117] overflow-hidden shadow-[0_20px_70px_-15px_rgba(0,0,0,0.5)] animate-fade-in">
                {/* Mac-style title bar */}
                <div className="flex items-center px-4 py-3 bg-[#161b22] border-b border-white/[0.06]">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-[#ff5f57] shadow-[0_0_6px_rgba(255,95,87,0.4)]"></div>
                    <div className="w-3 h-3 rounded-full bg-[#febc2e] shadow-[0_0_6px_rgba(254,188,46,0.4)]"></div>
                    <div className="w-3 h-3 rounded-full bg-[#28c840] shadow-[0_0_6px_rgba(40,200,64,0.4)]"></div>
                  </div>
                  <div className="flex-1 flex justify-center">
                    <span className="text-[20px] text-[#8b949e]">analyzer.ts</span>
                  </div>
                  <div className="w-[52px]"></div>
                </div>
                {/* Code with line numbers */}
                <div className="flex text-[13px] font-mono leading-[22px]">
                  {/* Line numbers */}
                  <div className="select-none text-right pr-4 pl-4 py-4 text-[#484f58] border-r border-white/[0.04]">
                    {Array.from({ length: 17 }, (_, i) => (
                      <div key={i}>{i + 1}</div>
                    ))}
                  </div>
                  {/* Code content */}
                  <div className="py-4 pl-5 pr-6 overflow-hidden">
                    <div><span className="text-[#ff7b72]">interface</span> <span className="text-[#79c0ff]">AnalysisResult</span> <span className="text-[#c9d1d9]">{'{'}</span></div>
                    <div><span className="text-[#c9d1d9]">{'  '}</span><span className="text-[#c9d1d9]">architecture</span><span className="text-[#c9d1d9]">: </span><span className="text-[#79c0ff]">Pattern</span><span className="text-[#c9d1d9]">[];</span></div>
                    <div><span className="text-[#c9d1d9]">{'  '}</span><span className="text-[#c9d1d9]">entryPoints</span><span className="text-[#c9d1d9]">: </span><span className="text-[#79c0ff]">string</span><span className="text-[#c9d1d9]">[];</span></div>
                    <div><span className="text-[#c9d1d9]">{'  '}</span><span className="text-[#c9d1d9]">complexity</span><span className="text-[#c9d1d9]">: </span><span className="text-[#79c0ff]">number</span><span className="text-[#c9d1d9]">;</span></div>
                    <div><span className="text-[#c9d1d9]">{'}'}</span></div>
                    <div>&nbsp;</div>
                    <div><span className="text-[#ff7b72]">async</span> <span className="text-[#ff7b72]">function</span> <span className="text-[#d2a8ff]">analyzeRepo</span><span className="text-[#c9d1d9]">(</span></div>
                    <div><span className="text-[#c9d1d9]">{'  '}</span><span className="text-[#ffa657]">repo</span><span className="text-[#c9d1d9]">: </span><span className="text-[#79c0ff]">Repository</span></div>
                    <div><span className="text-[#c9d1d9]">): </span><span className="text-[#79c0ff]">Promise</span><span className="text-[#c9d1d9]">{'<'}</span><span className="text-[#79c0ff]">AnalysisResult</span><span className="text-[#c9d1d9]">{'>'}</span> <span className="text-[#c9d1d9]">{'{'}</span></div>
                    <div><span className="text-[#8b949e]">{'  '}// Parse & build dependency graph</span></div>
                    <div><span className="text-[#c9d1d9]">{'  '}</span><span className="text-[#ff7b72]">const</span> <span className="text-[#79c0ff]">files</span> <span className="text-[#ff7b72]">=</span> <span className="text-[#ff7b72]">await</span> <span className="text-[#d2a8ff]">parseCodebase</span><span className="text-[#c9d1d9]">(</span><span className="text-[#ffa657]">repo</span><span className="text-[#c9d1d9]">);</span></div>
                    <div><span className="text-[#c9d1d9]">{'  '}</span><span className="text-[#ff7b72]">const</span> <span className="text-[#79c0ff]">graph</span> <span className="text-[#ff7b72]">=</span> <span className="text-[#d2a8ff]">buildGraph</span><span className="text-[#c9d1d9]">(</span><span className="text-[#79c0ff]">files</span><span className="text-[#c9d1d9]">);</span></div>
                    <div>&nbsp;</div>
                    <div><span className="text-[#c9d1d9]">{'  '}</span><span className="text-[#ff7b72]">return</span> <span className="text-[#c9d1d9]">{'{'}</span></div>
                    <div><span className="text-[#c9d1d9]">{'    '}architecture: </span><span className="text-[#d2a8ff]">detectPatterns</span><span className="text-[#c9d1d9]">(</span><span className="text-[#79c0ff]">graph</span><span className="text-[#c9d1d9]">),</span></div>
                    <div><span className="text-[#c9d1d9]">{'    '}entryPoints: </span><span className="text-[#d2a8ff]">findEntries</span><span className="text-[#c9d1d9]">(</span><span className="text-[#79c0ff]">files</span><span className="text-[#c9d1d9]">),</span></div>
                    <div><span className="text-[#c9d1d9]">{'    '}complexity: </span><span className="text-[#d2a8ff]">calcMetrics</span><span className="text-[#c9d1d9]">(</span><span className="text-[#79c0ff]">graph</span><span className="text-[#c9d1d9]">),</span></div>
                    <div><span className="text-[#c9d1d9]">{'  '}{'}'}</span><span className="text-[#c9d1d9]">;</span></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 bg-background-secondary">
        <div className="container mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Powerful Features for Developers
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Everything you need to understand and navigate complex codebases efficiently
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto">
            <Card className="border-border/50 hover:border-primary/50 transition-all duration-300 card-hover">
              <CardHeader>
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <FileCode className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="text-xl font-bold">Auto-Documentation</CardTitle>
                <CardDescription className="text-base leading-relaxed">
                  Automatically generate comprehensive documentation for any codebase using AI-powered analysis.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-border/50 hover:border-primary/50 transition-all duration-300 card-hover">
              <CardHeader>
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <Network className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="text-xl font-bold">Dependency Mapping</CardTitle>
                <CardDescription className="text-base leading-relaxed">
                  Visualize complex code relationships with interactive dependency graphs and flow diagrams.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-border/50 hover:border-primary/50 transition-all duration-300 card-hover">
              <CardHeader>
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <GitBranch className="h-6 w-6 text-primary" />
                </div>
                <CardTitle className="text-xl font-bold">Logic Explanation</CardTitle>
                <CardDescription className="text-base leading-relaxed">
                  Get instant answers about any part of the codebase through our intelligent chat interface.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-4">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Get Started in 3 Simple Steps
            </h2>
          </div>

          <div className="space-y-8">
            {[
              {
                step: "01",
                title: "Connect Your Repository",
                description: "Link your GitHub account or paste any public repository URL to get started.",
              },
              {
                step: "02",
                title: "AI Analyzes Your Code",
                description: "Our AI engine parses your codebase, identifies patterns, and builds a comprehensive knowledge graph.",
              },
              {
                step: "03",
                title: "Explore & Ask Questions",
                description: "Chat with your codebase, visualize dependencies, and understand complex logic instantly.",
              },
            ].map((item) => (
              <div key={item.step} className="flex gap-6 items-start group">
                <div className="flex-shrink-0 w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-2xl font-bold text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-300">
                  {item.step}
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                  <p className="text-muted-foreground">{item.description}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <Link href="/auth/login">
              <Button size="lg" className="gap-2">
                <Github className="h-5 w-5" />
                Get Started Now
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 py-8 px-4">
        <div className="container mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <FileCode className="h-5 w-5 text-primary" />
            <span className="font-semibold">CodeLens AI</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © 2026 CodeLens AI. Built for developers, by developers.
          </p>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <Link href="#" className="hover:text-foreground transition-colors">Privacy</Link>
            <Link href="#" className="hover:text-foreground transition-colors">Terms</Link>
            <Link href="#" className="hover:text-foreground transition-colors">Docs</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
