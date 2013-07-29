#
# LastFm JLD Data Analysis
# José Devezas (joseluisdevezas@gmail.com)
#
# Based on the Last.fm JLD Dataset, by José Devezas.
# Soon to be publish on: http://www.josedevezas.com/phd.
#

PlotUserNonZeroRatingDistribution <- function(csv.filename, plot.filename, width=5, height=3) {
  if (!require("ggplot2")) {
    install.packages("ggplot2")
    library("ggplot2")
  }
  
  d <- read.csv(csv.filename, header=FALSE, col.names=c("user.id", "item.id", "rating"))
  d <- aggregate(d$item.id, by=list(d$user.id), length)
  names(d) <- c("user.id", "non.zero.ratings")
  chart <- ggplot(d, aes(x=non.zero.ratings)) +
    geom_histogram(binwidth=10) +
    scale_x_continuous(breaks=seq(0, 200, 20)) +
    labs(x="Number of Artists", y="Number of Users")
  ggsave(chart, filename=plot.filename, width=width, height=height)
}

PlotUserNonZeroRatingDistribution("~/Desktop/lastfm-jld-dataset/lastfm-user_artist_count-1k_users_subset.csv",
                                  "~/Desktop/lastfm-jld-dataset/output/artists_distribution.png")

PlotUserNonZeroRatingDistribution("~/Desktop/lastfm-jld-dataset/lastfm-user_artist_count-1k_users_subset.csv",
                                  "~/Desktop/lastfm-jld-dataset/output/artists_distribution.pdf")