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
}

libs()

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
  print(ggplot(user.data, aes(x=date, y=count, fill=factor(artist))) + geom_bar(stat="identity") +
          guides(fill=guide_legend(nrow=10, title.hjust=0.4, title.theme=element_text(size=12, face="bold", angle=0))))
}

motifs <- function(dd, from=3, to=5) {
  
}

dd <- read.data("/Users/jldevezas/Desktop/lastfm-dump-SNAPSHOT-20130918T1023.db")
plot.time.series(prepare.time.series(dd, 1))
res <- mclapply(as.list(sort(unique(dd$user_id))), function(uid) prepare.time.series(dd, uid))
#plot.time.series(res[[1]])