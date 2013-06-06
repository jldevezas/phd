#
# Collaborative Filtering Experiments
# José Devezas (joseluisdevezas@gmail.com)
#
# Based on the Audioscrobbler -- Music Recommendation Data Sets.
# Available here: http://www-etud.iro.umontreal.ca/~bergstrj/audioscrobbler_data.html
#

if (!require("NMF")) {
  source("http://bioconductor.org/biocLite.R")
  biocLite()  
  install.packages("NMF");
  library(NMF)
  install.extras("NMF")
}


baseDir <- "~/Desktop/profiledata_06-May-2005"
outputDir <- "~/Desktop/profiledata_06-May-2005/output"


UserItemCountToMatrix <- function(df) {
  m <- matrix(nrow=length(unique(df[, 1])), ncol=length(unique(df[, 2])))
  rownames(m) <- unique(df[, 1])
  colnames(m) <- unique(df[, 2])
  
  for (user in rownames(m)) {
    user.items <- df[which(df[, 1] == user), ]
    m[user, as.character(user.items[, 2])] <- as.numeric(user.items[, 3])
  }
  
  return(m)
}


FillMissing <- function(m, method="cmean") {
  if (method == "cmean") {
    # Remove columns that are all NA.
    m <- m[ , which(colSums(is.na(m)) != nrow(m))]
    
    cmeans <- apply(m, 2, function(e) mean(e, na.rm=TRUE))
    
    m <- t(apply(m, 1, function(e) {
      idx <- which(is.na(e))
      e[idx] <- as.numeric(cmeans[names(e[idx])])
      return(e)
    }))
  }
}


plays <- read.delim(paste(baseDir, "user_artist_data.txt", sep="/"), sep=" ",
                    header=FALSE, nrow=3000, col.names=c("user", "artist", "count"))
ratings <- FillMissing(UserItemCountToMatrix(plays))

ratings.train <- FillMissing(t(apply(ratings, 1, function(e) {
  n <- length(e)
  idx <- sample(1:n, n %/% 2)
  e[idx] <- NA
  return(e)
})))

fact.svd <- svd(ratings.train)
fact.nmf <- nmf(ratings.train, 2)