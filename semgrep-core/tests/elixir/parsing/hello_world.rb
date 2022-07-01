module Hello 
  def hello
    IO.puts("Hello world!!")
  end

  def hello(world)
    str = "Hello" + world
    IO.puts(str)
  end
end
