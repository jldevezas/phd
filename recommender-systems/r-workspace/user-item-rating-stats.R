dd <- read.csv("~/Desktop/lastfm-jld-dataset/lastfm-user_artist_count-1k_users_subset.csv",
               head=F, col.names=c("user", "item", "rating"))

stats <- list(n.users=length(unique(dd$user)),
              n.items=length(unique(dd$item)),
              n.items.per.user=summary(aggregate(dd$item, by=list(dd$user), length)$x),
              n.users.per.item=summary(aggregate(dd$user, by=list(dd$item), length)$x),
              ratings.summary=summary(dd$rating))
print(stats)