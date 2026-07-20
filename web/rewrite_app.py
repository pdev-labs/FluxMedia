import re

with open("src/App.tsx", "r") as f:
    content = f.read()

# 1. Replace imports with React.lazy
imports_pattern = re.compile(r'import\s+{\s*([A-Za-z0-9_]+)\s*}\s+from\s+"(\./pages/[^"]+)";')

def repl_lazy(m):
    comp = m.group(1)
    path = m.group(2)
    return f'const {comp} = React.lazy(() => import("{path}").then(m => ({{ default: m.{comp} }})));'

new_content = imports_pattern.sub(repl_lazy, content)

# 2. Extract Routes to an inner component
routes_pattern = re.compile(r'(<Routes>.*?</Routes>)', re.DOTALL)
routes_match = routes_pattern.search(new_content)
routes_block = routes_match.group(1)

# Add AnimatePresence and page transition wrapper
routes_block = routes_block.replace('<Routes>', '<Routes location={location} key={location.pathname}>')

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
      <React.Suspense fallback={{<div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}}>
        {routes_block.replace(/<Route path="([^"]+)" element={{<([A-Za-z0-9_]+) \/>}} \/>/g, '<Route path="$1" element={{<PageTransition><$2 /></PageTransition>}} />')}
      </React.Suspense>
    </AnimatePresence>
  );
}};
'''
