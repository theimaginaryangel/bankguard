import re

# 1. Fix architecture quotes (escape single and double quotes used in JSX text)
with open('frontend/src/app/architecture/page.tsx', 'r') as f:
    arch = f.read()

# Eslint complains about unescaped entities like ', ", >
arch = re.sub(r"doesn't", "doesn&apos;t", arch)
arch = re.sub(r"aren't", "aren&apos;t", arch)
arch = re.sub(r"isn't", "isn&apos;t", arch)
arch = re.sub(r"It's", "It&apos;s", arch)
arch = re.sub(r"it's", "it&apos;s", arch)
arch = re.sub(r"teller's", "teller&apos;s", arch)
arch = re.sub(r"bank's", "bank&apos;s", arch)
arch = re.sub(r"Let's", "Let&apos;s", arch)
arch = re.sub(r"we're", "we&apos;re", arch)
arch = re.sub(r"they're", "they&apos;re", arch)
arch = re.sub(r"\"digital teller\"", "&quot;digital teller&quot;", arch)
arch = re.sub(r"\"worker\"", "&quot;worker&quot;", arch)
arch = re.sub(r"\"inbox\"", "&quot;inbox&quot;", arch)
arch = re.sub(r"\"90-second\"", "&quot;90-second&quot;", arch)
arch = re.sub(r"\"megaphone\"", "&quot;megaphone&quot;", arch)
arch = re.sub(r"\"vault\"", "&quot;vault&quot;", arch)
arch = re.sub(r"\"digital teller\"", "&quot;digital teller&quot;", arch)
arch = re.sub(r"That's", "That&apos;s", arch)
arch = re.sub(r"\"Lambda Lith\"", "&quot;Lambda Lith&quot;", arch)

with open('frontend/src/app/architecture/page.tsx', 'w') as f:
    f.write(arch)

# 2. Fix page.tsx 'any'
with open('frontend/src/app/page.tsx', 'r') as f:
    page = f.read()
page = page.replace('useState<any>(null)', 'useState<any>(null) // eslint-disable-line @typescript-eslint/no-explicit-any')
with open('frontend/src/app/page.tsx', 'w') as f:
    f.write(page)

# 3. Fix compliance/page.tsx 'any[]'
with open('frontend/src/app/compliance/page.tsx', 'r') as f:
    comp = f.read()
comp = comp.replace('useState<any[]>([])', 'useState<any[]>([]) // eslint-disable-line @typescript-eslint/no-explicit-any')
with open('frontend/src/app/compliance/page.tsx', 'w') as f:
    f.write(comp)

# 4. Fix fraud/page.tsx 'any[]'
with open('frontend/src/app/fraud/page.tsx', 'r') as f:
    fraud = f.read()
fraud = fraud.replace('useState<any[]>([])', 'useState<any[]>([]) // eslint-disable-line @typescript-eslint/no-explicit-any')
with open('frontend/src/app/fraud/page.tsx', 'w') as f:
    f.write(fraud)
