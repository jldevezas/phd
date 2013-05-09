#
# Configurations and constants.
#

baseDir <- "~/Desktop/lastfm-dataset-1K"

# Dates range from 2005-02-14 00:00:07 to 2013-09-29 18:32:04.
maxMonthRange <- c("2005-02", "2013-09")


#
# Utility functions.
#

IsAnyNA <- function(vals) {
  for(val in vals)
    if (is.na(val))
      return(TRUE)
  return(FALSE)
}

AddZeroMonths <- function(d, month.range=NA) {
  if (IsAnyNA(month.range))
    month.range <- range(d$month)
    
  all.months <- as.character(seq(as.Date(paste(month.range[1], "01", sep="-")),
                                as.Date(paste(month.range[2], "01", sep="-")),
                                by="1 month"))
  all.months <- unlist(lapply(all.months, function(month) {
    d <- strsplit(month, "-")[[1]]
    paste(d[1], d[2], sep="-")
  }))
  all.artists <- unique(d$artist)
  
  result <- data.frame(month = c(sapply(all.months, function(m) rep(m, length(all.artists)))))
  result <- cbind(result, artist = rep(all.artists, length(all.months)))
  result <- merge(d, result, by.x=c("month", "artist"), by.y=c("month", "artist"), all.y=TRUE)
  na.pos <- which(is.na(result$plays))
  if (length(na.pos) > 0)
    result[na.pos,]$plays <- 0  
  
  return(result)
}


#
# Dataset analysis.
#

users <- read.table(gzfile(paste(baseDir, "userid-profile.tsv.gz", sep="/")), quote="", sep="\t")
names(users) <- c("id", "gender", "age", "country", "registered")

#-------

user.stats <- data.frame(id=levels(users$id),
                        unique.artists=rep(NA, nrow(users)),
                        plays.total=rep(NA, nrow(users)),
                        plays.min=rep(NA, nrow(users)),
                        plays.qua1=rep(NA, nrow(users)),
                        plays.median=rep(NA, nrow(users)),
                        plays.mean=rep(NA, nrow(users)),
                        plays.qua3=rep(NA, nrow(users)),
                        plays.max=rep(NA, nrow(users)))

monthly.artist.plays <- list()
monthly.ranks <- list()
adoption.by.rank <- list()

for (user.id in users$id) {
  print(paste("Processing ", user.id, "...", sep=""))
  
  # Songs listened by the user.
  songs <- read.table(paste(paste(baseDir, user.id, sep="/"), "csv", sep="."), quote="", sep="\t", fill=T)
  names(songs) <- c("id", "timestamp", "artid", "artname", "traid", "traname")
  songs$month <- strftime(as.Date(songs$timestamp), "%Y-%m")
  
  # Monthly number of plays for each artist.
  monthly.artist.plays[[user.id]] <- with(songs, aggregate(artname, by=list(month, artname), length))
  names(monthly.artist.plays[[user.id]]) <- c("month", "artist", "plays")
  
  # Unique artists listened by the user.
  user.stats[which(user.stats$id == user.id),]$unique.artists <- nlevels(monthly.artist.plays[[user.id]]$artist)
  
  # Statistics for the play count of the user.
  user.stats[which(user.stats$id == user.id),]$plays.total <- sum(monthly.artist.plays[[user.id]]$plays)
  user.stats[which(user.stats$id == user.id), 4:9] <- summary(monthly.artist.plays[[user.id]]$plays)
        
  # Monthly artist ranks.
  monthly.ranks[[user.id]] <- aggregate(songs$artname, by=list(songs$month), function(artname) {
    plays <- table(artname)
    names(sort(plays, decreasing=TRUE))
  })
  names(monthly.ranks[[user.id]]) <- c("month", "ranks")
    
  # How well do favorite monthly artists rank ahead in time?
  # (This score measures adpotion by considering not only if an artist is listened to again
  # in the future, but also how much it's listened to compared to other artists.)
  user.adoption.by.rank <- list()
  for (i in 1:(nrow(monthly.ranks[[user.id]]$ranks))) {
    user.adoption.by.rank[[monthly.ranks[[user.id]]$ranks[i, 1]]] <- 0
    for (j in 1:(nrow(monthly.ranks[[user.id]]$ranks))) {
      if (i < j & monthly.ranks[[user.id]]$month[i] < monthly.ranks[[user.id]]$month[j]) {
        if (monthly.ranks[[user.id]]$ranks[i, 1] %in% monthly.ranks[[user.id]]$ranks[j,]) {
          user.adoption.by.rank[[monthly.ranks[[user.id]]$ranks[i, 1]]] <-
            user.adoption.by.rank[[monthly.ranks[[user.id]]$ranks[i, 1]]] + 1 * 1/j
        }
      }
    }
  }
  user.adoption.by.rank <- sort(unlist(user.adoption.by.rank)/max(unlist(user.adoption.by.rank)), decreasing=TRUE)
  adoption.by.rank[[user.id]] <- user.adoption.by.rank
  
  # How consistently are favorite monthly artists listened to ahead in time?
  # (Measure variance ahead of time?)
}


#
# Write results to files.
#
                   
write.csv(user.stats, file=paste(baseDir, "user-stats.csv", sep="/"), row.names=FALSE)                   

for (user.id in users$id) {
  print(paste("Writing analysis data for ", user.id, "...", sep=" "))
  
  # Top overall artists.
  overall.ranks <- with(monthly.artist.plays[[user.id]], aggregate(artist, by=list(artist), length))
  names(overall.ranks) <- c("artist", "plays")
  overall.ranks <- overall.ranks[order(overall.ranks$plays, decreasing=T),]
  
  # Fill the monthly time series with zeros for missing values and export to CSV.
  write.csv(AddZeroMonths(monthly.artist.plays[[user.id]][
    which(monthly.artist.plays[[user.id]]$artist %in% overall.ranks[1:20, ]$artist),]),
          file=paste(paste(baseDir, user.id, sep="/"), "_monthly_activity.csv", sep=""),
          row.names=FALSE)
}


#
# Clean up temporary variables.
#

rm(i, j, user.id, plays, month, artists, overall.ranks, songs)