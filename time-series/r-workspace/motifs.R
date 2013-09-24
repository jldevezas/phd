libs <- function() {
  if (!require(sqldf)) {
    install.packages("sqldf")
    library(sqldf)
  }
  
  if (!require(ggplot2)) {
    install.packages("ggplot2")
    library(ggplot2)
  }
  
  if (!require(parallel)) {
    install.packages("parallel")
    library(parallel)
  }
  
  if (!require(dtw)) {
    install.packages("dtw")
    library(dtw)
  }
  
  if (!require(cluster)) {
    install.packages("cluster")
    library(cluster)
  }
}

read.data <- function(path) {
  dd <- sqldf("SELECT user_id, artist, timestamp FROM tracks", dbname=path)
  dd$date <- as.POSIXct(dd$timestamp, origin="1970-01-01")
  dd$time <- strftime(dd$date, "%H:%M:%S")
  dd$week <- strftime(dd$date, "%W")
  dd$date <- as.Date(strftime(dd$date, "%Y-%m-%d"))
  return(dd)
}

top.artists <- function(dd, n=10) {
  top <- aggregate(dd$artist, by=list(dd$artist), length)
  names(top) <- c("artist", "count")
  return(top[order(top$count, decreasing=TRUE), ][1:n, ]$artist)
}

prepare.time.series <- function(dd, user_id) {
  dv <- dd[which(dd$user_id == user_id), ]
  dv <- dv[which(dv$artist %in% top.artists(dv, 20)), ]
  res <- aggregate(dv$artist, by=list(artist=dv$artist, date=dv$date), length)
  names(res) <- c("artist", "date", "count")
  
  all.dates <- seq.Date(min(res$date) - 2, max(res$date) + 2, by="1 day")
  all.artists <- sort(unique(dv$artist))
  base <- data.frame(artist=unlist(lapply(all.artists, function(a) rep(a, length(all.dates)))),
                     date=rep(all.dates, length(all.artists)))
  res <- merge(base, res, by=c("date", "artist"), all.x=TRUE)
  res[is.na(res$count), ]$count <- 0  
  res <- res[order(res$artist, res$date), c(2,1,3)]
  
  return(res)
}

plot.time.series <- function(user.data) {
  print(ggplot(user.data, aes(x=date, y=count, fill=factor(artist))) +
          geom_bar(stat="identity") +
          scale_fill_discrete("Artists") +
          labs(x="Date", y="Play Count") +
          guides(fill=guide_legend(nrow=10, title.hjust=0.4, title.theme=element_text(size=12, face="bold", angle=0))))
}

best.clustering <- function(hclust.result, hclust.dist) {
  best.cl <- NULL
  best.sil <- 0
  for (h in 0:max(hclust.result$height)) {
    cl <- cutree(hclust.result, h=h)
    sil <- summary(silhouette(cl, hclust.dist))$avg.width
    if (sil > best.sil) {
      best.sil <- sil
      best.cl <- cl
    }
  }
  
  return(best.cl)
}

clustering.to.list <- function(cl, m) {
  res <- list()
  for (idx in 1:length(cl)) {
    group <- as.character(cl[[idx]])
    if (is.null(res[[group]])) {
      res[[group]] <- m[idx, ]
    } else {
      res[[group]] <- rbind(res[[group]], m[idx, ])
    }
  }
  return(res)
}

motifs <- function(dd, sizes=c(3,5,10)) {
  artists = sort(unique(dd$artist))
  dates = sort(unique(dd$date))
  m <- matrix(0, nrow=length(dates), ncol=length(artists))
  colnames(m) <- artists
  rownames(m) <- as.character(dates)
  m[as.character(dates), artists] <- dd[unlist(lapply(artists, function(a) which(dd$artist == a))), ]$count
  m <- t(m)
  
  all.res <- list()
  for (size in sizes) {
    res <- NULL
    for (i in 1:(ncol(m)-size)) {
      res <- rbind(res, m[, i:(i+size-1)])
    }
    res <- as.matrix(res)
    colnames(res) <- 1:size
    res <- res[which(rowSums(res) > 0), ]
    dist.matrix <- dist(res, method="DTW")
    names(dist.matrix) <- NULL
    hc <- hclust(dist.matrix, method="average")
    best <- best.clustering(hc, dist.matrix)
    
    all.res[[size]] <- clustering.to.list(best, res)
  }
  return(all.res)
}

libs()
dd <- read.data("/Users/jldevezas/Desktop/lastfm-dump-SNAPSHOT-20130918T1023.db")
res <- mclapply(as.list(sort(unique(dd$user_id))), function(uid) prepare.time.series(dd, uid))
plot.time.series(res[[1]])
