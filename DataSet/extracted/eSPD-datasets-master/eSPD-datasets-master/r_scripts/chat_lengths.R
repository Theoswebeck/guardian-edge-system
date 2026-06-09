# Load the package required to read JSON files.
library("rjson")

BASE_DIR = "~/sshfs/code/Datasets/"
result <- fromJSON(file = paste(sep="", BASE_DIR, "PANC/statistics/segment-lengths-PANC.json"))
positive = result[["predator"]]
negative = result[["non-predator"]]

ylim=2000

breaks = seq(0,150,1)
par(mar=c(5, 6, 4, 4) + 0.1)

all = c(positive, negative)

allh = hist(
  main = "Segment length distribution in PANC",
  xlab = "Number of messages",
  ylab = "Frequency among kinds of segments",
  all,         breaks=breaks, col=scales::alpha('black',.3),      border=F, yaxt="n", xaxt="n",xlim=c(1,xlim), ylim=c(0,ylim)
)
hist(negative, breaks=breaks, add=T,col=scales::alpha('blue',.3), border=F, yaxt="n", xaxt="n",xlim=c(1,xlim), ylim=c(0,ylim))
hist(positive, breaks=breaks, add=T,col=scales::alpha('red',.4),  border=F, yaxt="n", xaxt="n",xlim=c(1,xlim), ylim=c(0,ylim))

axis(1, at=c(1, seq(10, xlim, 10)), cex.axis=0.75)
axis(2, at=c(1, seq(1000, ylim, 1000)), cex.axis=0.75)

cols = c(
  scales::alpha('red',.3),
  scales::alpha('blue',.3),
  scales::alpha('black',.3)
)
legend(110, 1400, legend=c(
  "positive segments",
  "negative segments",
  "all segments"
), col=cols, pch = 15, text.width=27, cex=1)

dev.copy(pdf, paste(sep="", BASE_DIR, 'PANC/statistics/segment_length_distribution.pdf'), height=5, width=11)
dev.off()
