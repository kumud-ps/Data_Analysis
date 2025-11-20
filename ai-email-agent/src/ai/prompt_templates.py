from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class EmailType(Enum):
    """Enumeration of different email types."""
    BUSINESS_INQUIRY = "business_inquiry"
    PERSONAL_MESSAGE = "personal_message"
    SUPPORT_REQUEST = "support_request"
    MEETING_REQUEST = "meeting_request"
    JOB_APPLICATION = "job_application"
    SALES_PITCH = "sales_pitch"
    NEWSLETTER = "newsletter"
    UNCLEAR = "unclear"
    SPAM = "spam"


@dataclass
class PromptTemplate:
    """Template for AI response prompts."""
    system_prompt: str
    user_prompt_template: str
    response_examples: list = None
    constraints: list = None


class EmailPromptTemplates:
    """Collection of prompt templates for different email types."""

    @staticmethod
    def get_business_inquiry_template() -> PromptTemplate:
        """Template for business inquiry responses."""
        return PromptTemplate(
            system_prompt="You are a professional assistant responding to business inquiries. Be helpful, professional, and concise. Provide accurate information or appropriate next steps.",
            user_prompt_template="""
            Generate a professional response to this business inquiry:

            From: {sender_name} ({sender_email})
            Subject: {subject}

            Email content:
            {email_body}

            Guidelines:
            - Acknowledge their inquiry professionally
            - Provide relevant information or next steps
            - Keep it concise and business-appropriate
            - Include a clear call to action if needed
            - Be helpful but avoid making promises you can't keep
            """,
            response_examples=[
                "Thank you for your interest. I've received your inquiry and will get back to you within 24 hours.",
                "I appreciate you reaching out. Let me connect you with the right person who can help with this."
            ],
            constraints=[
                "Keep response under 200 words",
                "Maintain professional tone",
                "Don't make commitments without authority"
            ]
        )

    @staticmethod
    def get_personal_message_template() -> PromptTemplate:
        """Template for personal message responses."""
        return PromptTemplate(
            system_prompt="You are an assistant responding to personal messages. Be warm, friendly, and appropriate for personal communication.",
            user_prompt_template="""
            Generate a friendly response to this personal message:

            From: {sender_name} ({sender_email})
            Subject: {subject}

            Message content:
            {email_body}

            Guidelines:
            - Acknowledge their message warmly
            - Respond to any questions or points they made
            - Keep the tone friendly and personal
            - Be genuine and authentic
            - Consider the relationship context
            """,
            response_examples=[
                "Thanks for your message! It was great to hear from you.",
                "I appreciate you reaching out. Let me know if there's anything I can help with."
            ],
            constraints=[
                "Keep response under 150 words",
                "Maintain warm, personal tone",
                "Be genuine and authentic"
            ]
        )

    @staticmethod
    def get_support_request_template() -> PromptTemplate:
        """Template for support request responses."""
        return PromptTemplate(
            system_prompt="You are a helpful support assistant. Provide clear, helpful information to resolve their issue or guide them to the right resources.",
            user_prompt_template="""
            Generate a helpful response to this support request:

            From: {sender_name} ({sender_email})
            Subject: {subject}

            Support request:
            {email_body}

            Guidelines:
            - Acknowledge their issue and show empathy
            - Provide clear steps to resolve the problem
            - Offer additional help if needed
            - Be professional and supportive
            - Include relevant contact information for further help
            """,
            response_examples=[
                "I understand you're experiencing an issue. Let me help you resolve this step by step.",
                "Thanks for reaching out about this. Here's what you can do to fix this issue."
            ],
            constraints=[
                "Focus on practical solutions",
                "Use simple, clear language",
                "Provide specific action steps"
            ]
        )

    @staticmethod
    def get_meeting_request_template() -> PromptTemplate:
        """Template for meeting request responses."""
        return PromptTemplate(
            system_prompt="You are an assistant managing meeting requests. Be clear, organized, and helpful with scheduling.",
            user_prompt_template="""
            Generate a response to this meeting request:

            From: {sender_name} ({sender_email})
            Subject: {subject}

            Meeting request:
            {email_body}

            Guidelines:
            - Acknowledge their meeting request
            - Address their suggested times or propose alternatives
            - Ask for agenda if not provided
            - Confirm meeting format (in-person, video call, phone)
            - Be clear about availability and next steps
            """,
            response_examples=[
                "Thanks for the meeting request. I'm available at the suggested time and have confirmed on my calendar.",
                "I'd be happy to meet. The proposed time doesn't work for me, but I'm available at these alternatives."
            ],
            constraints=[
                "Be specific about availability",
                "Propose concrete alternatives if needed",
                "Request agenda if unclear"
            ]
        )

    @staticmethod
    def get_unclear_request_template() -> PromptTemplate:
        """Template for unclear or ambiguous requests."""
        return PromptTemplate(
            system_prompt="You are an assistant responding to unclear emails. Ask for clarification politely and help guide the conversation.",
            user_prompt_template="""
            Generate a response asking for clarification about this unclear email:

            From: {sender_name} ({sender_email})
            Subject: {subject}

            Unclear request:
            {email_body}

            Guidelines:
            - Acknowledge their message politely
            - Identify what information you need to help them
            - Ask specific, clarifying questions
            - Be helpful and patient
            - Suggest ways they can provide more details
            """,
            response_examples=[
                "Thanks for your message. To help you better, could you provide more details about what you're looking for?",
                "I want to make sure I understand your request correctly. Could you clarify a few points?"
            ],
            constraints=[
                "Ask specific clarifying questions",
                "Be patient and helpful",
                "Don't make assumptions"
            ]
        )

    @staticmethod
    def get_default_template() -> PromptTemplate:
        """Default template for general email responses."""
        return PromptTemplate(
            system_prompt="You are a helpful email assistant. Generate appropriate, polite, and useful responses.",
            user_prompt_template="""
            Generate an appropriate response to this email:

            From: {sender_name} ({sender_email})
            Subject: {subject}

            Email content:
            {email_body}

            Guidelines:
            - Acknowledge their message
            - Respond appropriately to their content
            - Be polite and helpful
            - Keep the response concise
            - Include appropriate next steps if needed
            """,
            response_examples=[
                "Thank you for your message. I've received it and will respond appropriately.",
                "Thanks for reaching out. I appreciate you taking the time to write."
            ],
            constraints=[
                "Keep response under 200 words",
                "Maintain appropriate tone",
                "Be helpful and constructive"
            ]
        )

    @classmethod
    def get_template(cls, email_type: EmailType) -> PromptTemplate:
        """Get the appropriate template for the given email type."""
        template_methods = {
            EmailType.BUSINESS_INQUIRY: cls.get_business_inquiry_template,
            EmailType.PERSONAL_MESSAGE: cls.get_personal_message_template,
            EmailType.SUPPORT_REQUEST: cls.get_support_request_template,
            EmailType.MEETING_REQUEST: cls.get_meeting_request_template,
            EmailType.UNCLEAR: cls.get_unclear_request_template,
        }

        method = template_methods.get(email_type, cls.get_default_template)
        return method()

    @classmethod
    def build_prompt(
        cls,
        email_type: EmailType,
        sender_name: str,
        sender_email: str,
        subject: str,
        email_body: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """Build system and user prompts for email response generation."""
        template = cls.get_template(email_type)

        system_prompt = template.system_prompt

        # Add any additional context to the system prompt
        if additional_context:
            context_items = []
            if 'relationship' in additional_context:
                context_items.append(f"Relationship context: {additional_context['relationship']}")
            if 'previous_interactions' in additional_context:
                context_items.append(f"Previous interactions: {additional_context['previous_interactions']}")
            if 'user_preferences' in additional_context:
                context_items.append(f"User preferences: {additional_context['user_preferences']}")

            if context_items:
                system_prompt += "\n\nAdditional context:\n" + "\n".join(context_items)

        # Build user prompt with template variables
        user_prompt = template.user_prompt_template.format(
            sender_name=sender_name or "Unknown",
            sender_email=sender_email or "unknown@email.com",
            subject=subject or "No subject",
            email_body=email_body or "No content"
        )

        # Add constraints to user prompt if they exist
        if template.constraints:
            constraints_text = "\n\nAdditional constraints:\n" + "\n".join([f"- {c}" for c in template.constraints])
            user_prompt += constraints_text

        return system_prompt, user_prompt


class ResponseStyleGuide:
    """Style guidelines for different types of responses."""

    @staticmethod
    def get_formal_style_guidelines() -> str:
        """Get guidelines for formal communication style."""
        return """
        Formal Communication Style:
        - Use proper salutations (Dear, Sincerely, Best regards)
        - Avoid contractions (use "do not" instead of "don't")
        - Use complete sentences and proper grammar
        - Be respectful and professional
        - Avoid slang or casual expressions
        - Keep paragraphs concise and well-structured
        """

    @staticmethod
    def get_casual_style_guidelines() -> str:
        """Get guidelines for casual communication style."""
        return """
        Casual Communication Style:
        - Use friendly greetings (Hi, Hello, Hey)
        - Contractions are acceptable
        - Can be more conversational
        - Still be respectful but less formal
        - Appropriate for familiar contacts
        - Keep tone warm and approachable
        """

    @staticmethod
    def get_business_style_guidelines() -> str:
        """Get guidelines for business communication style."""
        return """
        Business Communication Style:
        - Professional but not overly formal
        - Clear and concise
        - Focus on efficiency and results
        - Include relevant business context
        - Appropriate use of business terminology
        - Maintain professional boundaries
        """