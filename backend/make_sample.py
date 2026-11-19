from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

lines = [
    "Climate change is one of the most pressing issues of our time.",
    "Rising global temperatures are causing sea levels to rise and weather patterns to shift.",
    "Many governments have set targets to cut emissions by the end of the decade.",
    "Renewable energy now supplies a growing share of electricity.",
    "Further research is needed on large scale energy storage.",
]

c = canvas.Canvas("sample.pdf", pagesize=A4)
c.setFont("Helvetica", 11)
y = 780
for line in lines:
    c.drawString(50, y, line)
    y -= 22
c.save()
print("sample.pdf created")