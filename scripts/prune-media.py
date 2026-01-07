import os
import shutil


def run():
    the_source = "/mnt/media-1/video/movies"
    the_dest = "/mnt/media-5/video/movies/"
    the_movies_src = os.listdir(the_source)
    the_movies_dest = os.listdir(the_dest)
    dupes = 0
    for movie_src in the_movies_src:
        if movie_src in the_movies_dest:
            dupes += 1
            movie_path=os.path.join(the_source, movie_src)
            print(movie_path)
            if os.path.isdir(movie_path):
                shutil.rmtree(movie_path)
            else:
                os.remove(movie_path)

    print("\n Total SRC: %s" % len(the_movies_src))
    print("Total DEST: %s" % len(the_movies_dest))
    print("Dupes: %s" % dupes)


if __name__ == "__main__":
    run()
~