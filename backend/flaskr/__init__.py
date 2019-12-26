import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
  '''
  paginate questions to return in 
  groups of 10 at a time
  '''
  page = request.args.get('page', 1, type=int)
  start =  (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  pagination = questions[start:end]

  return pagination

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app, resources={r'/api/*': {'origins': '*'}})
 
  # CORS Headers
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PATCH, POST, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
  
  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/api/categories')
  def get_all_categories():
    try:
      categories = Category.query.all()
      if len(categories) == 0:
        abort(404)

      format_categories = [category.format() for category in categories]
      return jsonify({
        "success": True,
        "categories": format_categories,
        # "total_categories": len(categories)
      }), 200

    except Exception as e:
      abort(500)
    finally:
      db.session.close()

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/api/questions')
  def get_questions():
    try:
      questions_selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, questions_selection)
      categories = Category.query.all()
      formatted_categories = [category.format() for category in categories]

      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(Question.query.all()),
        'categories': formatted_categories,
        'current_category': categories[0].format()
      }), 200
    except Exception as e:
      abort(422)

  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''

  @app.route('/api/question/<int:question_id>', methods=["DELETE"])
  def delete_question(question_id):
    try:
      question = Question.query.filter_by(id = question_id).one_or_none()
      if question is None:
        abort(404)
      question.delete()
      db.session.commit()
      return jsonify({
          'success': True,
          'id': question_id,
          'total_questions': len(Question.query.all())
      }), 200
    except Exception as e:
      abort(422)
      db.session.rollback()
    finally:
      db.session.commit()

  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''

  @app.route('/api/questions', methods=['POST'])
  def create_question():
    try:
      body = request.get_json()
      search_term = body.get('searchTerm', None)
      if search_term is not None:
        '''
        Gets a list of search
        '''
        categories = Category.query.all()
        questions_search = Question.query.filter(Question.question.ilike('%{}%'.format(search_term))).all()
        paginated_questions = paginate_questions(request, questions_search)
        format_categories = [category.format() for category in categories]
        return jsonify({
          'success': True,
          'questions': paginated_questions,
          'total_questions': len(Question.query.all()),
          'categories': format_categories,
          'current_category': categories[0].format()
            }), 200
      else:
        try:
          '''
          Creates a new Question when search not found
          '''
          question = body.get('question', None)
          answer = body.get('answer', None)
          difficulty = body.get('difficulty', None)
          category = body.get('category', None)
          new_question = Question(question=question, answer=answer, difficulty=difficulty, category=category)
          new_question.insert()
          return jsonify({
            'success': True,
            'created': new_question.id,
            'total_questions': len(Question.query.all())
              }), 201
        except Exception as e:
          db.session.rollback()
        finally:
          db.session.commit()

    except:
      abort(422)
  
  @app.route('/api/categories/<string:category_id>/questions')
  def get_questions_by_category(category_id):
    category = Category.query.get(category_id)
    if category is None:
        abort(404)
    try:
      questions_selection = Question.query.filter(Question.category == category.id).all()
      current_questions = paginate_questions(request, questions_selection)
      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(questions_selection),
        'current_category': category.format()
      }), 200
    except:
      abort(422)

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/api/quiz', methods=['POST'])
  def get_quizzes():
    '''
    return questions based on the specified category if applicable.
    questions returned previously are not repeated.
    The questions are returned one at a time.
    '''
    try:
      body = request.get_json()
      questions = Question.query.filter_by(
        category=body.get("quiz_category")["id"]
      ).filter(Question.id.notin_(body.get      ("previous_questions"))).all()

      if body.get("quiz_category")["id"] == 0:
        questions = Question.query.filter(
          Question.id.notin_(body.get("previous_questions"))).all()

      question = None

      if questions:
        question = random.choice(questions).format()

      return jsonify({
          "success": True,
          "question": question
  }), 200
    except:
      abort(404)
  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 404,
      "message": "Resource was not found"
      }), 404

  @app.errorhandler(422)
  def entity_not_processed(error):
    return jsonify({
      "success": False, 
      "error": 422,
      "message": "Unprocessable Entity!"
      }), 422

  @app.errorhandler(500)
  def server_error(error):
    return jsonify({
      "success": False, 
      "error": 500,
      "message": "Internal Server Error!"
      }), 500
  
  return app

    