import re

with open("src/App.tsx", "r") as f:
    content = f.read()

# Add framer-motion and react-router-dom useLocation imports
if "framer-motion" not in content:
    content = content.replace('import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";', 'import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";\nimport { AnimatePresence, motion } from "framer-motion";')

# Replace imports with React.lazy
imports_pattern = re.compile(r'import\s+{\s*([A-Za-z0-9_]+)\s*}\s+from\s+"(\./pages/[^"]+)";')
def repl_lazy(m):
    comp = m.group(1)
    path = m.group(2)
    return f'const {comp} = React.lazy(() => import("{path}").then(m => ({{ default: m.{comp} }})));'

content = imports_pattern.sub(repl_lazy, content)

# Extract Routes
routes_pattern = re.compile(r'(<Routes>.*?</Routes>)', re.DOTALL)
routes_match = routes_pattern.search(content)
if not routes_match:
    print("No routes found")
    exit(1)

routes_block = routes_match.group(1)
routes_block = routes_block.replace('<Routes>', '<Routes location={location} key={location.pathname}>')

# Replace elements with PageTransition wrapper
def wrap_route(m):
    return f'<Route path="{m.group(1)}" element={{<PageTransition><{m.group(2)} /></PageTransition>}} />'

routes_block_wrapped = re.sub(r'<Route path="([^"]+)" element=\{<([A-Za-z0-9_]+) \/>\} \/>', wrap_route, routes_block)

app_routes_component = f'''
const PageTransition: React.FC<{{ children: React.ReactNode }}> = ({{ children }}) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    transition={{ duration: 0.2 }}
  >
    {{children}}
  </motion.div>
);

const AppRoutes: React.FC = () => {{
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <React.Suspense fallback={{<div className="flex items-center justify-center h-full min-h-[400px]"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}}>
        {routes_block_wrapped}
      </React.Suspense>
    </AnimatePresence>
  );
}};
'''

content = routes_pattern.sub('<AppRoutes />', content)
content = content.replace('export const App: React.FC = () => {', app_routes_component + '\nexport const App: React.FC = () => {')

with open("src/App.tsx", "w") as f:
    f.write(content)

print("Updated App.tsx successfully.")
