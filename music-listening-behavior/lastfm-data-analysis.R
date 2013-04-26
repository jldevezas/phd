baseDir = "~/Desktop/lastfm-dataset-1K"

is.any.na = function(vals) {
  for(val in vals)
    if (is.na(val))
      return(TRUE)
  return(FALSE)
}

f.expand.artists.months.with.zeros = function(d, month.range=NA) {
  if (is.any.na(month.range))
    month.range = range(d$month)
    
  all.months = as.character(seq(as.Date(paste(month.range[1], "01", sep="-")),
                                as.Date(paste(month.range[2], "01", sep="-")),
                                by="1 month"))
  all.months = unlist(lapply(all.months, function(month) { d = strsplit(month, "-")[[1]]; paste(d[1], d[2], sep="-") }))
  all.artists = unique(d$artist)
  
  result = data.frame(month = c(sapply(all.months, function(m) rep(m, length(all.artists)))))
  result = cbind(result, artist = rep(all.artists, length(all.months)))
  result = merge(d, result, by.x=c("month", "artist"), by.y=c("month", "artist"), all.y=TRUE)
  na.pos = which(is.na(result$plays))
  if (length(na.pos) > 0)
    result[na.pos,]$plays = 0  
  
  return(result)
}

f.expand.artists.days.with.zeros = function(d, day.range=NA) {
  if (is.any.na(day.range))
    day.range = range(d$day)
  
  all.days = as.character(seq(as.Date(day.range[1]), as.Date(day.range[2]), by="1 day"))
  all.artists = unique(d$artist)
  
  result = data.frame(day = c(sapply(all.days, function(m) rep(m, length(all.artists)))))
  result = cbind(result, artist = rep(all.artists, length(all.days)))
  result = merge(d, result, by.x=c("day", "artist"), by.y=c("day", "artist"), all.y=TRUE)
  na.pos = which(is.na(result$plays))
  if (length(na.pos) > 0)
    result[na.pos,]$plays = 0
  
  return(result)
}

# Dates range from 2005-02-14 00:00:07 to 2013-09-29 18:32:04.
max.month.range = c("2005-02", "2013-09")

users = read.table(gzfile(paste(baseDir, "userid-profile.tsv.gz", sep="/"), quote="", sep="\t")
names(users) = c("id", "gender", "age", "country", "registered")

#for (userId in users$id[which(users$id == "user_000001"):length(users$id)]) {
for (userId in users$id) {
  print(paste("Processing ", userId, "...", sep=""))
  # Data for user 1 only (users were cut into separate files using split-by-user.py).
  songs = read.table(paste(paste(baseDir, userId, sep="/"), "csv", sep="."), quote="", sep="\t", fill=T)
  names(songs) = c("id", "timestamp", "artid", "artname", "traid", "traname")
  songs$month = strftime(as.Date(songs$timestamp), "%Y-%m")
  #songs$day = strftime(as.Date(songs$timestamp), "%Y-%m-%d")
  
  # Monthly number of plays for each artist.
  monthly.artist.plays = with(songs, aggregate(artname, by=list(month, artname), length))
  names(monthly.artist.plays) = c("month", "artist", "plays")
  
  # Daly number of plays for each artist.
  #daily.artist.plays = with(songs, aggregate(artname, by=list(day, artname), length))
  #names(daily.artist.plays) = c("day", "artist", "plays")
    
  # Top overall artists.
  overall.ranks = with(monthly.artist.plays, aggregate(artist, by=list(artist), length))
  names(overall.ranks) = c("artist", "plays")
  overall.ranks = overall.ranks[order(overall.ranks$plays, decreasing=T),]
  
  # Fill the monthly time series with zeros for missing values and export to CSV.
  write.csv(f.expand.artists.months.with.zeros(monthly.artist.plays[
    which(monthly.artist.plays$artist %in% overall.ranks[1:20, ]$artist),]),
            file=paste(paste(baseDir, userId, sep="/"), "_monthly_activity.csv", sep=""),
            row.names=FALSE)
  
  # Fill the daily time series with zeros for missing values and export to CSV.
  #write.csv(f.expand.artists.days.with.zeros(daily.artist.plays[
  #  which(daily.artist.plays$artist %in% overall.ranks[1:20, ]$artist),]),
  #          file=paste(paste(baseDir, userId, sep="/"), "_daily_activity.csv", sep=""),
  #          quote=FALSE, row.names=FALSE)
    
  # Monthly favorite artists.
  monthly.favorite = with(monthly.artist.plays, aggregate(plays, by=list(month), function(monthly.plays) artist[which.max(monthly.plays)]))
  names(monthly.favorite) = c("month", "artist")
  monthly.favorite$artist = as.character(monthly.favorite$artist)

  # Monthly artist ranks.
  monthly.ranks = aggregate(songs$artname, by=list(songs$month), function(artname) {
    plays = table(artname)
    names(sort(plays, decreasing=TRUE))
  })
  names(monthly.ranks) = c("month", "ranks")
  
  # How well do favorite monthly artists rank ahead in time?
  # (This score measures adpotion by considering not only if an artist is listened to again
  # in the future, but also how much it's listened to compared to other artists.)
  adoption.by.rank = list()
  for (i in 1:(nrow(monthly.ranks$ranks))) {
    adoption.by.rank[[monthly.ranks$ranks[i,1]]] = 0
    for (j in 1:(nrow(monthly.ranks$ranks))) {
      if (i < j & monthly.ranks$month[i] < monthly.ranks$month[j]) {
        if (monthly.ranks$ranks[i,1] %in% monthly.ranks$ranks[j,]) {
          adoption.by.rank[[monthly.ranks$ranks[i,1]]] = adoption.by.rank[[monthly.ranks$ranks[i,1]]] + 1 * 1/j
        }
      }
    }
  }
  adoption.by.rank = sort(unlist(adoption.by.rank)/max(unlist(adoption.by.rank)), decreasing=TRUE)
  
  # How consistently are favorite monthly artists listened to ahead in time?
  # (Measure variance ahead of time?)
  # result = list()
  # for (i in 1:(nrow(monthly.favorite)-1)) {
  #   result[[monthly.favorite[i,]$artist]] = mean(result[[monthly.favorite[i,]$artist]],
  #     var(monthly.artist.plays[which(
  #       monthly.artist.plays$month > monthly.favorite[i,]$month
  #       & monthly.artist.plays$artist == monthly.favorite[i,]$artist),]$plays), na.rm=TRUE)
  # }
  # result = sort(unlist(result), decreasing=TRUE)
}