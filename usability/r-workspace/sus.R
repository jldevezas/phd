analyze <- function(sus.q) {
  sus.q[, seq(1, length(sus.q), by=2)] <- sus.q[, seq(1, length(sus.q), by=2)] - 1
  sus.q[, seq(2, length(sus.q), by=2)] <- 5 - sus.q[, seq(2, length(sus.q), by=2)]
  
  sus <- apply(sus.q, 1, sum) * 2.5
  print(summary(sus))
  hist(sus, xlim=c(0,100))
}

eval <- read.csv("~/Desktop/juggle-eval.csv")

first.iteration <- 1:7
second.iteration <- 8:nrow(eval)

sus.q <- eval[, 6:15]

analyze(sus.q[first.iteration, ])
analyze(sus.q[second.iteration, ])