from django.shortcuts import render
from .models import Post
from .serializers import PostSerializer
from consumptions.serializers import ConsumptionSerializer
from consumptions.models import Consumption
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from datetime import datetime

# Date를 이용하여 Post에 접근하는 뷰 -> GET, POST 메서드
class PostDateView(APIView):
  # 날짜로 해당 post 가져오는 메서드
  def get_post(self, request, date):
    try:
      post = Post.objects.get(author=self.request.user, created_at=date)
      return post
    except Post.DoesNotExist:
      return None

  def get(self, request):
    date = self.request.GET.get('date', None)
    # 존재하지 않는 날짜 쿼리 시 예외처리
    if date is None:
      data = {
        'error_msg' : '올바른 날짜를 입력하세요.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)
    # Date Format 변환
    date = datetime.fromtimestamp(int(date)/1000)
    post = self.get_post(self, date)
    if post is not None:
      consumptions = Consumption.objects.filter(post=post.id)
       # Queryset to JSON
      data = consumptions.values()
      return Response(data=data) 
    else:
      data = {
        'error_msg' : '해당 날짜에 작성된 포스트가 존재하지 않습니다.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)

  def post(self, request):
    # 아무 값도 입력하지 않았을 때 예외처리(400 에러 리턴)
    if request.data['meal'] == []:
      data = {
        'empty_value_error' : '최소 한 끼는 반드시 입력해야 합니다.'
      }
      return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

    # 날짜 변환: unix timestamp string(1660575600000) -> datetime
    request.data['created_at'] = datetime.fromtimestamp(int(request.data['created_at'])/1000)
    
    # 1. postSerializer 통해 역직렬화하여 값을 DB에 저장 -> Post 객체 생성
    serializer = PostSerializer(data=request.data)
    print(serializer)
    if serializer.is_valid():
      post = serializer.save(
        author=request.user
      )
      post_serializer = PostSerializer(post).data
      
      # 2. 포스트가 생성되고 난 뒤에 그 다음에 해당 post id를 가지고 Post_Consumption 테이블 지정
      for elem in request.data['meal']:
        # 방금 생성된 포스트의 pk값 가져오기
        post_id = post_serializer['id']
        # 입력받은 값들을 consumption 객체의 각 필드에 입력
        food_id = elem[0]
        food_amount = elem[1]
        meal_type = elem[2]
        # TODO : 이미지를 올리고 이미지의 url을 저장

        consumption_data = {
          'post' : post_id,
          'food' : food_id,
          'amount' : food_amount,
          'meal_type' : meal_type,
        }

        consumption_serializer = ConsumptionSerializer(data=consumption_data)
        if consumption_serializer.is_valid():
          # consumption 객체 생성
          consumption_serializer.save()
        else:
          return Response(status=status.HTTP_400_BAD_REQUEST, data=consumption_serializer.errors)

      return Response(data=post_serializer, status=status.HTTP_200_OK)
    else:
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ID(PK)를 이용하여 Post에 접근하는 뷰 -> GET, PUT 메서드 처리
class PostIdView(APIView):

  # pk로 해당 post 가져오는 메서드
  def get_post_by_id(self, pk):
    try:
      post = Post.objects.get(pk=pk)
      return post
    except Post.DoesNotExist:
      return None

  def get(self, request, pk):

    post = self.get_post_by_id(pk)
    if post is not None:
      
      # 예외처리
      if post.author != request.user:
        data = {
          'error_msg' : '포스트의 작성자가 아닙니다.'
        }
        return Response(status=status.HTTP_403_FORBIDDEN, data=data)

      consumptions = Consumption.objects.filter(post=post.id)
       # Queryset to JSON
      data = consumptions.values()
      return Response(data=data)

    else:
      data = {
        'error_msg' : '해당 날짜에 작성된 포스트가 존재하지 않습니다.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)

  # create 처럼 내부에서 ConsumptionSerialzer(update 메서드) 이용
  # 또 다른 방법 : post_pk로 걸려있는 consumpton들을 찾아낸 뒤에 각각에 대해 수정?
  # 지금 방법이 맞는 것일 수도..
  def put(self, request, pk):
    
    post = self.get_post_by_id(pk)
    if post is not None:
      if post.author != request.user:
        data = {
          'error_msg' : '포스트의 작성자가 아닙니다.'
        }
        return Response(status=status.HTTP_403_FORBIDDEN, data=data)
      
      consumptions = Consumption.objects.filter(post=post.id)
      # print(consumptions)
      print(len(consumptions)) # target
      print(len(request.data['meal'])) # input
      for i in range(len(request.data['meal'])):
        # 빈 리스트인 것은 생략(그대로 보존)
        if request.data['meal'][i] == []:
            continue
        # 입력받은 데이터
        data = {
          'post' : post.id,
          'food' : request.data['meal'][i][0],
          'amount' : request.data['meal'][i][1],
          'meal_type' : request.data['meal'][i][2]
        }
        
        # 수정하려는 consumption의 수보다 request.data의 수가 작거나 같을 때에만 해당 쌍에 맞춰서 업데이트 진행
        if i < len(consumptions):
          consumption_update_serializer = ConsumptionSerializer(consumptions[i], data=data, partial=True)
          # print(request.data['meal'][i])
          if consumption_update_serializer.is_valid():
            # 각 consumption 객체 update
            consumption_update_serializer.save()
          else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=consumption_update_serializer.errors)
        # 수정하려는 consumption의 수보다 request.data의 수가 더 많으면 추가로 생성
        else: 
          consumption_create_serializer = ConsumptionSerializer(data=data)
          if consumption_create_serializer.is_valid():
            consumption_create_serializer.save()

      consumptions = Consumption.objects.filter(post=post.id) # 해당 포스트에 걸려있는 섭취정보 다 가져옴
      return Response(data=consumptions.values(), status=status.HTTP_200_OK)
    else:
      data = {
        'error_msg' : '포스트가 존재하지 않습니다.'
      }
      return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

      # for i in range()
      # serializer = ConsumptionSerializer()