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

read.data <- function(path) {
  dd <- sqldf("SELECT user_id, artist, timestamp FROM tracks", dbname=path)
  dd$date <- as.POSIXct(dd$timestamp, origin="1970-01-01")
  dd$time <- strftime(dd$date, "%H:%M:%S")
  dd$date <- as.Date(strftime(dd$date, "%Y-%m-%d"))  
  return(dd)
}

prepare.time.series <- function(dd, user_id) {
  dv <- dd[which(dd$user_id == user_id), ]
  res <- aggregate(dv$artist, by=list(date=dv$date, artist=dv$artist), length)
  names(res) <- c("date", "artist", "count")
  
  base <- data.frame(date=seq.Date(min(res$date) - 2, max(res$date) + 2, by="1 day"))
  res <- merge(base, res, by="date", all.x=TRUE)
  res[is.na(res$count), ]$count <- 0
  
  return(res[order(res$date), ])
}

plot.time.series <- function(user.data) {
  print(ggplot(user.data, aes(x=date, y=count)) + geom_line())
}

cl <- makeCluster(getOption('cl.cores', detectCores() * 2))
clusterEvalQ(cl, {
  library(sqldf)
  
  read.data <- function(path) {
    dd <- sqldf("SELECT user_id, artist, timestamp FROM tracks", dbname=path)
    dd$date <- as.POSIXct(dd$timestamp, origin="1970-01-01")
    dd$time <- strftime(dd$date, "%H:%M:%S")
    dd$date <- as.Date(strftime(dd$date, "%Y-%m-%d"))  
    return(dd)
  }
  
  prepare.time.series <- function(dd, user_id) {
    dv <- dd[which(dd$user_id == user_id), ]
    res <- aggregate(dv$artist, by=list(date=dv$date, artist=dv$artist), length)
    names(res) <- c("date", "artist", "count")
    
    base <- data.frame(date=seq.Date(min(res$date) - 2, max(res$date) + 2, by="1 day"))
    res <- merge(base, res, by="date", all.x=TRUE)
    res[is.na(res$count), ]$count <- 0
    
    return(res[order(res$date), ])
  }
  
  dd <- read.data("/Users/jldevezas/Desktop/lastfm-dump-SNAPSHOT-20130918T1023.db")
})
res <- parSapply(cl, sort(unique(dd$user_id)), FUN=function(user_id) { prepare.time.series(dd, user_id) })
stopCluster(cl)

u1 <- prepare.time.series(dd, 1)
plot.time.series(u1)