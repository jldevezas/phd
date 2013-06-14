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

if (!require("irlba")) {
  install.packages("irlba")
  library(irlba)
}

if (!require("scidb")) {
  install.packages("scidb")
  library(scidb)
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


FillMissing <- function(m, method="colmean") {
  if (method == "colmean") {
    # Remove columns that are all NA.
    m <- m[ , which(colSums(is.na(m)) != nrow(m))]
    
    cmeans <- apply(m, 2, function(e) mean(e, na.rm=TRUE))
    
    m <- t(apply(m, 1, function(e) {
      idx <- which(is.na(e))
      e[idx] <- as.numeric(cmeans[names(e[idx])])
      return(e)
    }))
  } else if (method == "zeros") {
    m[which(is.na(m))] <- 0
  }
  
  return(m)
}


CosineSimilarity <- function(a, b) {
  sum(a * b) / (norm(as.matrix(a), "F") * norm(as.matrix(b), "F"))
}


SvdPredictRating <- function(ratings, user.latent.features, user.idx, item.idx, method="cosine") {
  candidate.users.idx <- as.numeric(which(ratings[ , item.idx] != 0))
  
  sim <- c()
  user.features <- user.latent.features[user.idx, ]
  for (candidate.user.idx in candidate.users.idx) {
    candidate.user.features <- user.latent.features[candidate.user.idx, ]
    if (method == "pearson") {
      sim <- c(sim, cor(user.features, candidate.user.features, method="pearson"))
    } else if (method == "cosine") {
      sim <- c(sim, CosineSimilarity(user.features, candidate.user.features))
    }
  }
  
  most.similar.user.idx <- candidate.users.idx[which.max(sim)]
  predicted.rating <- ratings[most.similar.user.idx, item.idx]
  
  res <- list(user.idx=user.idx,
              item.idx=item.idx,
              nr.candidate.users=length(candidate.users.idx))
  
  if (length(sim) > 0) {
    res$candidate.users.idx=candidate.users.idx
    res$candidate.users.similarities=sim
    res$most.similar.user.idx=most.similar.user.idx
    res$predicted.rating=predicted.rating
  }
  
  return(res)
}


plays <- read.delim(paste(baseDir, "user_artist_data.txt", sep="/"), sep=" ",
                    header=FALSE, nrow=1000, col.names=c("user", "artist", "count"))

# Original data (used for testing).
ratings <- FillMissing(UserItemCountToMatrix(plays), method="zeros")

# Base data.
ratings.train <- FillMissing(t(apply(ratings, 1, function(e) {
  n <- length(e)
  idx <- sample(1:n, n %/% 2)
  e[idx] <- NA
  return(e)
})), method="zeros")

fact.svd <- svd(ratings.train)

# Randomly select a rated item that isn't rated in the training set.
ratings.test.idx <- which(ratings.train == 0 & ratings != 0, arr.ind=TRUE)
test.user.item <- ratings.test.idx[sample(1:nrow(ratings.test.idx), 1), ]
names(test.user.item) <- c("user.idx", "item.idx")
test.user.idx <- as.numeric(test.user.item)[1]
test.item.idx <- as.numeric(test.user.item)[2]
res.svd <- SvdPredictRating(ratings.train, fact.svd$u %*% diag(fact.svd$d), test.user.idx, test.item.idx)

# Evaluate based on the difference of each candidate rating compared to real rating.
# A better value should be the closest to the real value.
# According to this, results aren't that great (tried it a few times with different random items).
abs(ratings[res.svd$user.idx, res.svd$item.idx] - ratings[res.svd$candidate.users.idx, res.svd$item.idx])
abs(ratings[res.svd$user.idx, res.svd$item.idx] - res.svd$predicted.rating)

# NOTE This is too slow for large data.
#fact.nmf <- nmf(ratings.train, 2)