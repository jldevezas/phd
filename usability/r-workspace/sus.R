analyze.usability <- function(sus.q, plots=TRUE) {
#   require(ggplot2)
  
  sus.q[, seq(1, length(sus.q), by=2)] <- sus.q[, seq(1, length(sus.q), by=2)] - 1
  sus.q[, seq(2, length(sus.q), by=2)] <- 5 - sus.q[, seq(2, length(sus.q), by=2)]
  
  sus <- apply(sus.q, 1, sum) * 2.5
    
  if (plots) {
    hist(sus, xlim=c(0,100), xlab="SUS Score", ylab="Nummber of Users",
         main="SUS Score Distribution", col="WhiteSmoke")
#     print(qplot(sus, geom="histogram", binwidth=10, xlim=c(0,100), xlab="SUS Value", ylab="Number of Users"))
  }
  
  return(list(sus=sus, sus.summary=summary(sus), sus.std=sd(sus)))
}

analyze.recs <- function(recs, plots=TRUE, profile.size.threshold=NULL) {
#   require(ggplot2)
  
  lrecs <- recs
  
  if (is.numeric(profile.size.threshold)) {
    lrecs <- lrecs[which(recs$Profile.Size >= profile.size.threshold), ]
  }
  
  cor.m <- cor(lrecs)
  colnames(cor.m) <- NULL
  rownames(cor.m) <- NULL

  if (plots) {
    par(mfrow=c(2,2))
    
    hist(lrecs[, 1], xlim=c(0, 10), col="WhiteSmoke",
         xlab="Quality Score",
         ylab="Number of Users",
         main="Quality of Recommendations")
    
    hist(lrecs[, 2], xlim=c(0, 30), col="WhiteSmoke",
         xlab="Number of Awful Recommendations",
         ylab="Number of Users",
         main="Awuful Recommendations")
    
    hist(lrecs[, 3], xlim=c(0, 30), col="WhiteSmoke",
         xlab="Number of Great Recommendations",
         ylab="Number of Users",
         main="Great Recommendations")
    
    hist(lrecs[, 4], xlim=c(0, 30), col="WhiteSmoke",
         xlab="Number of Captivating New Recommendations",
         ylab="Number of Users",
         main="Captivating New Recommendations")

#     print(qplot(lrecs[, 1], geom="histogram", binwidth=1, xlim=c(0, 10),
#                 xlab="Quality of Recommendations", ylab="Number of Users"))
#     print(qplot(lrecs[, 2], geom="histogram", binwidth=3, xlim=c(0, 30),
#                 xlab="Number of Awful Recommendations", ylab="Number of Users"))
#     print(qplot(lrecs[, 3], geom="histogram", binwidth=3, xlim=c(0, 30),
#                 xlab="Number of Great Recommendations", ylab="Number of Users"))
#     print(qplot(lrecs[, 4], geom="histogram", binwidth=3, xlim=c(0, 30),
#                 xlab="Number of Captivating New Recommendations", ylab="Number of Users"))
  }
  
  return(list(recs.summary=summary(lrecs), recs.std=sapply(lrecs, sd), cor.matrix=cor.m))
}

eval <- read.csv("~/Desktop/juggle-eval.csv")

first.iteration <- 1:7
second.iteration <- 8:nrow(eval)

sus.q <- eval[, 6:15]

par(mfrow=c(1,2))
analyze.usability(sus.q[first.iteration, ])
analyze.usability(sus.q[second.iteration, ])

recs <- eval[, 16:(ncol(eval)-1)]
analyze.recs(recs)
analyze.recs(recs, profile.size.threshold=10)
