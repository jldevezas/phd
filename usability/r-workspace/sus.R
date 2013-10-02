eval <- read.csv("~/Desktop/juggle-eval.csv")

sus.q <- eval[, 6:15]
sus.q[, seq(1, length(sus.q), by=2)] <- sus.q[, seq(1, length(sus.q), by=2)] - 1
sus.q[, seq(2, length(sus.q), by=2)] <- 5 - sus.q[, seq(2, length(sus.q), by=2)]
sus <- apply(sus.q, 1, sum) * 2.5
summary(sus)